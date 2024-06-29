# Copyright (C) 2024 Bellande Robotics Sensors Research Innovation Center, Ronaldson Bellande
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
import requests
import cv2
import numpy as np
import base64
from sensor_msgs.msg import Image
from cv_bridge import CvBridge



def object_detection(image):
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(image, desired_encoding="bgr8")

    _, img_encoded = cv2.imencode('.jpg', cv_image)
    img_base64 = base64.b64encode(img_encoded).decode('utf-8')

    payload = {
        "image": img_base64,
        "task": "object_detection"
    }

    headers = {
        "Authorization": f"Bearer {api_access_key}"
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        for obj in result['objects']:
            label = obj['label']
            confidence = obj['confidence']
            x, y, w, h = obj['bbox']
            cv2.rectangle(cv_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(cv_image, f"{label}: {confidence:.2f}", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        return bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None



def image_callback(msg):
    processed_img = object_detection(msg)
    if processed_img:
        pub.publish(processed_img)



def main():
    global api_url, api_access_key ,pub

    config_file_path = os.path.join(os.path.dirname(__file__), '../config/configs.json')
    if not os.path.exists(config_file_path):
        print("Config file not found:", config_file_path)
        return
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
        url = config['url']
        endpoint_path = config['endpoint_path']["object_detection"]
        api_access_key = config["Bellande_Framework_Access_Key"]
    
    if ros_version == "1":
        rospy.init_node('object_detection_node', anonymous=True)
        pub = rospy.Publisher('object_detection_result', Image, queue_size=10)
        sub = rospy.Subscriber('camera/image_raw', Image, image_callback)
    elif ros_version == "2":
        rclpy.init()
        node = rclpy.create_node('object_detection_node')
        pub = node.create_publisher(Image, 'object_detection_result', 10)
        sub = node.create_subscription(Image, 'camera/image_raw', image_callback, 10)

    api_url = f"{url}{endpoint_path}"

    try:
        print("Object detection node is running. Ctrl+C to exit.")
        if ros_version == "1":
            rospy.spin()
        elif ros_version == "2":
            rclpy.spin(node)
    except KeyboardInterrupt:
        print("Shutting down object detection node.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if ros_version == "2":
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    ros_version = os.getenv("ROS_VERSION")
    if ros_version == "1":
        import rospy
    elif ros_version == "2":
        import rclpy
    main()
