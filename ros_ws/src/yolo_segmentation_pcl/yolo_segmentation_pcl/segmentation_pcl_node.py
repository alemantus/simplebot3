import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
from yolo_msgs.msg import DetectionArray
import numpy as np
import cv2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
import message_filters
import tf2_ros
from tf2_ros import TransformException


class SegmentationPCLNode(Node):
    def __init__(self):
        super().__init__('segmentation_pcl_node')

        self.declare_parameter('yolo_topic', 'yolo/detections')
        self.declare_parameter('depth_topic', '/femto_bolt/depth/image_raw')
        self.declare_parameter('depth_camera_info_topic', '/femto_bolt/depth/camera_info')
        self.declare_parameter('color_camera_info_topic', '/femto_bolt/camera_info')
        self.declare_parameter('depth_unit_scale', 0.001)
        self.declare_parameter('outlier_z_threshold', 0.05)
        
        # Keep these for legacy or very minor tweaks, but default to 0
        self.declare_parameter('mask_offset_x', 0.0) 
        self.declare_parameter('mask_offset_y', 0.0) 

        self.yolo_topic = self.get_parameter('yolo_topic').value
        self.depth_topic = self.get_parameter('depth_topic').value
        self.depth_info_topic = self.get_parameter('depth_camera_info_topic').value
        self.color_info_topic = self.get_parameter('color_camera_info_topic').value
        
        self.get_logger().info(f"Subscribing to YOLO: {self.yolo_topic}, Depth: {self.depth_topic}")

        # TF2 Setup
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.detection_sub = message_filters.Subscriber(
            self, DetectionArray, self.yolo_topic, qos_profile=qos_profile_sensor_data)
        self.depth_sub = message_filters.Subscriber(
            self, Image, self.depth_topic, qos_profile=qos_profile_sensor_data)

        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.detection_sub, self.depth_sub], 10, 0.5)
        self.ts.registerCallback(self.callback)

        self.depth_camera_info = None
        self.color_camera_info = None

        self.depth_info_sub = self.create_subscription(
            CameraInfo, self.depth_info_topic, self.depth_info_callback, qos_profile_sensor_data)
        self.color_info_sub = self.create_subscription(
            CameraInfo, self.color_info_topic, self.color_info_callback, qos_profile_sensor_data)

        self.pcl_pub = self.create_publisher(
            PointCloud2, '/yolo/segmented_pointcloud', qos_profile_sensor_data)
        
        self.detections_3d_pub = self.create_publisher(
            DetectionArray, '/yolo/detections_3d', qos_profile_sensor_data)

    def depth_info_callback(self, msg):
        self.depth_camera_info = msg

    def color_info_callback(self, msg):
        self.color_camera_info = msg

    def callback(self, detections_msg, depth_msg):
        if self.depth_camera_info is None or self.color_camera_info is None:
            return

        # 1. Get Transform from Color Optical Frame to Depth Optical Frame
        try:
            trans = self.tf_buffer.lookup_transform(
                depth_msg.header.frame_id,
                self.color_camera_info.header.frame_id,
                rclpy.time.Time())
            
            q = trans.transform.rotation
            t = trans.transform.translation
            
            # Manual quaternion to rotation matrix
            sqw, sqx, sqy, sqz = q.w**2, q.x**2, q.y**2, q.z**2
            invs = 1 / (sqx + sqy + sqz + sqw)
            R = np.array([
                [(sqx - sqy - sqz + sqw) * invs, 2 * (q.x*q.y - q.z*q.w) * invs, 2 * (q.x*q.z + q.y*q.w) * invs],
                [2 * (q.x*q.y + q.z*q.w) * invs, (-sqx + sqy - sqz + sqw) * invs, 2 * (q.y*q.z - q.x*q.w) * invs],
                [2 * (q.x*q.z - q.y*q.w) * invs, 2 * (q.y*q.z + q.x*q.w) * invs, (-sqx - sqy + sqz + sqw) * invs]
            ])
            T = np.array([t.x, t.y, t.z])
            
        except TransformException as ex:
            self.get_logger().warn(f'Could not transform color to depth: {ex}', throttle_duration_sec=5.0)
            return

        # 2. Decode depth image
        scale = self.get_parameter('depth_unit_scale').value
        try:
            if depth_msg.encoding == '16UC1':
                depth_image = np.frombuffer(depth_msg.data, dtype=np.uint16).reshape(
                    depth_msg.height, depth_msg.width).astype(np.float32)
            elif depth_msg.encoding == '32FC1':
                depth_image = np.frombuffer(depth_msg.data, dtype=np.float32).reshape(
                    depth_msg.height, depth_msg.width).copy()
                scale = 1.0
            else:
                return
        except:
            return

        h, w = depth_image.shape
        cfx, cfy, ccx, ccy = self.color_camera_info.k[0], self.color_camera_info.k[4], self.color_camera_info.k[2], self.color_camera_info.k[5]
        dfx, dfy, dcx, dcy = self.depth_camera_info.k[0], self.depth_camera_info.k[4], self.depth_camera_info.k[2], self.depth_camera_info.k[5]

        # Prepare 3D Detections Output
        output_detections = DetectionArray()
        output_detections.header = depth_msg.header
        
        all_points = []
        off_x = self.get_parameter('mask_offset_x').value
        off_y = self.get_parameter('mask_offset_y').value
        z_threshold = self.get_parameter('outlier_z_threshold').value

        for det in detections_msg.detections:
            if not (hasattr(det, 'mask') and det.mask.data):
                continue
            
            # --- Pass 1: Build approx mask to get Z ---
            obj_mask_approx = np.zeros((h, w), dtype=np.uint8)
            mw = det.mask.width if det.mask.width > 0 else self.color_camera_info.width
            mh = det.mask.height if det.mask.height > 0 else self.color_camera_info.height
            mfx, mfy = cfx * (mw/self.color_camera_info.width), cfy * (mh/self.color_camera_info.height)
            mcx, mcy = ccx * (mw/self.color_camera_info.width), ccy * (mh/self.color_camera_info.height)
            
            pts_approx = []
            for p in det.mask.data:
                u_d = (p.x - mcx) * (dfx/mfx) + dcx
                v_d = (p.y - mcy) * (dfy/mfy) + dcy
                pts_approx.append([int(np.clip(u_d, 0, w-1)), int(np.clip(v_d, 0, h-1))])
            
            if not pts_approx: continue
            cv2.fillPoly(obj_mask_approx, [np.array(pts_approx, dtype=np.int32)], 255)
            
            rows, cols = np.where(obj_mask_approx > 0)
            z_vals = depth_image[rows, cols] * scale
            valid_z = z_vals[np.isfinite(z_vals) & (z_vals > 0.1)]
            if len(valid_z) == 0: continue
            z_est = np.median(valid_z)
            
            # --- Pass 2: Accurate Projection ---
            obj_mask_acc = np.zeros((h, w), dtype=np.uint8)
            pts_acc = []
            for p in det.mask.data:
                ray_c = np.array([(p.x - mcx) * z_est / mfx, (p.y - mcy) * z_est / mfy, z_est])
                point_d = R @ ray_c + T
                u_d = point_d[0] * dfx / point_d[2] + dcx + off_x
                v_d = point_d[1] * dfy / point_d[2] + dcy + off_y
                pts_acc.append([int(np.clip(u_d, 0, w-1)), int(np.clip(v_d, 0, h-1))])
            
            cv2.fillPoly(obj_mask_acc, [np.array(pts_acc, dtype=np.int32)], 255)
            
            # Extract 3D points for this object
            rows, cols = np.where(obj_mask_acc > 0)
            z = depth_image[rows, cols] * scale
            valid = np.isfinite(z) & (z > 0.1)
            rows, cols, z = rows[valid], cols[valid], z[valid]
            if len(z) == 0: continue
            
            z_med = np.median(z)
            inliers = np.abs(z - z_med) < z_threshold
            rows, cols, z = rows[inliers], cols[inliers], z[inliers]
            if len(z) == 0: continue
            
            obj_x = (cols - dcx) * z / dfx
            obj_y = (rows - dcy) * z / dfy
            obj_cloud = np.stack([obj_x, obj_y, z], axis=1).astype(np.float32)
            all_points.append(obj_cloud)
            
            # Calculate Centroid (using median for robustness)
            cx, cy, cz = np.median(obj_x), np.median(obj_y), np.median(z)
            
            # Populate BBox3D
            det.bbox3d.center.position.x = float(cx)
            det.bbox3d.center.position.y = float(cy)
            det.bbox3d.center.position.z = float(cz)
            det.bbox3d.frame_id = depth_msg.header.frame_id
            
            output_detections.detections.append(det)

        # Publish Results
        if output_detections.detections:
            self.detections_3d_pub.publish(output_detections)

        if all_points:
            combined_cloud = np.concatenate(all_points, axis=0)
            header = Header()
            header.stamp = depth_msg.header.stamp
            header.frame_id = depth_msg.header.frame_id
            self.pcl_pub.publish(point_cloud2.create_cloud_xyz32(header, combined_cloud))



def main(args=None):
    rclpy.init(args=args)
    node = SegmentationPCLNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
