import sys
import subprocess
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QRect, QTimer
from PIL import Image

class DongleTouchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dongle Touch Controller")
        self.resize(1280, 900)  # Height no longer needs to accommodate button specifically

        self.start_pos = None
        self.screenshot_path = "screen.png"

        self.device_width = 480
        self.device_height = 854

        self.original_image = None
        self.scaled_pixmap = None
        self.image_rect = QRect()

        # Streaming mode flag & timer
        self.streaming = False
        self.stream_interval_ms = 1000  # 1 second default
        self.stream_timer = QTimer()
        self.stream_timer.timeout.connect(self.update_screenshot)

        # Rotation angle in degrees (0, 90, 180, 270)
        self.rotation_angle = 0

        # Layout & Widgets
        self.layout = QVBoxLayout(self)
        # Removed Enter button, so nothing added here

        self.update_screenshot()

    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        self.update()
        super().resizeEvent(event)

    def update_screenshot(self):
        try:
            if not self.take_screenshot():
                print("Failed to take screenshot.")
                return
            img = Image.open(self.screenshot_path)
            self.original_image = img
            self.update_scaled_pixmap()
            os.remove(self.screenshot_path)
            print("Screenshot updated.")
            self.update()
        except Exception as e:
            print(f"Error updating screenshot: {e}")

    def take_screenshot(self):
        try:
            ret1 = subprocess.run(
                ['adb', 'shell', 'screencap', f'/sdcard/{self.screenshot_path}'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
            )
            if ret1.returncode != 0:
                print(f"adb screencap error: {ret1.stderr.decode().strip()}")
                return False

            ret2 = subprocess.run(
                ['adb', 'pull', f'/sdcard/{self.screenshot_path}', self.screenshot_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
            )
            if ret2.returncode != 0:
                print(f"adb pull error: {ret2.stderr.decode().strip()}")
                return False

            subprocess.run(['adb', 'shell', 'rm', f'/sdcard/{self.screenshot_path}'],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            return True
        except Exception as e:
            print(f"Failed getting screenshot via file method: {e}")
            return False

    def update_scaled_pixmap(self):
        if not self.original_image:
            return

        img = self.original_image.copy()
        if self.rotation_angle != 0:
            img = img.rotate(self.rotation_angle, expand=True)

        widget_width = self.width()
        # Removed button height subtraction since no button
        widget_height = self.height()
        widget_aspect = widget_width / widget_height

        # Adjust device width/height based on rotation
        if self.rotation_angle in [90, 270]:
            device_width = self.device_height
            device_height = self.device_width
        else:
            device_width = self.device_width
            device_height = self.device_height

        device_aspect = device_width / device_height

        if widget_aspect > device_aspect:
            new_height = widget_height
            new_width = int(new_height * device_aspect)
        else:
            new_width = widget_width
            new_height = int(new_width / device_aspect)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        qimage = self.pil2pixmap(img)

        self.scaled_pixmap = qimage

        x = (widget_width - new_width) // 2
        y = (widget_height - new_height) // 2
        self.image_rect = QRect(x, y, new_width, new_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('black'))

        if self.scaled_pixmap:
            painter.drawPixmap(self.image_rect, self.scaled_pixmap)

    def pil2pixmap(self, im):
        im = im.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qimage = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    def map_to_device_coords(self, pos):
        if not self.original_image or self.scaled_pixmap is None:
            return -1, -1

        if not self.image_rect.contains(pos):
            return -1, -1

        x_in_image = pos.x() - self.image_rect.x()
        y_in_image = pos.y() - self.image_rect.y()

        x_ratio = self.device_width / self.image_rect.width()
        y_ratio = self.device_height / self.image_rect.height()

        # Calculate device coordinates before rotation
        x = x_in_image * x_ratio
        y = y_in_image * y_ratio

        # Adjust coordinates based on rotation angle
        if self.rotation_angle == 0:
            dev_x, dev_y = int(x), int(y)
        elif self.rotation_angle == 90:
            dev_x = int(self.device_width - y)
            dev_y = int(x)
        elif self.rotation_angle == 180:
            dev_x = int(self.device_width - x)
            dev_y = int(self.device_height - y)
        elif self.rotation_angle == 270:
            dev_x = int(y)
            dev_y = int(self.device_height - x)
        else:
            dev_x, dev_y = int(x), int(y)  # fallback

        # Clamp coordinates inside device bounds
        dev_x = max(0, min(self.device_width - 1, dev_x))
        dev_y = max(0, min(self.device_height - 1, dev_y))

        return dev_x, dev_y

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            x, y = self.map_to_device_coords(event.pos())
            if x >= 0 and y >= 0:
                self.send_tap(x, y)
            self.update_screenshot()

    def mouseMoveEvent(self, event):
        if self.start_pos and (event.buttons() & Qt.LeftButton):
            current_pos = event.pos()
            dx = current_pos.x() - self.start_pos.x()
            dy = current_pos.y() - self.start_pos.y()
            dist = (dx**2 + dy**2)**0.5

            if dist < 5:  # ignore tiny movements
                return

            start_x, start_y = self.map_to_device_coords(self.start_pos)
            end_x, end_y = self.map_to_device_coords(current_pos)

            if -1 not in (start_x, start_y, end_x, end_y):
                self.send_swipe(start_x, start_y, end_x, end_y)
                self.start_pos = current_pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = None
            self.update_screenshot()

    def wheelEvent(self, event):
        pos = event.pos()
        if not self.image_rect.contains(pos):
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        scroll_distance = 150
        swipe_x = self.device_width // 2

        if delta > 0:
            start_y = self.device_height // 2 - scroll_distance // 2
            end_y = self.device_height // 2 + scroll_distance // 2
        else:
            start_y = self.device_height // 2 + scroll_distance // 2
            end_y = self.device_height // 2 - scroll_distance // 2

        try:
            subprocess.run(
                ['adb', 'shell', 'input', 'swipe',
                 str(swipe_x), str(start_y),
                 str(swipe_x), str(end_y), '150'],
                timeout=5
            )
            print(f"Sent scroll swipe from ({swipe_x},{start_y}) to ({swipe_x},{end_y})")
        except Exception as e:
            print(f"Failed to send scroll swipe: {e}")

    def send_tap(self, x, y):
        if x < 0 or y < 0:
            return

        try:
            subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)], timeout=5)
            print(f"Sent tap to ({x},{y})")
        except Exception as e:
            print(f"Failed to send tap: {e}")

    def send_swipe(self, start_x, start_y, end_x, end_y):
        if start_x < 0 or start_y < 0 or end_x < 0 or end_y < 0:
            return

        try:
            subprocess.run(
                ['adb', 'shell', 'input', 'swipe', str(start_x), str(start_y), str(end_x), str(end_y), '300'],
                timeout=10
            )
            print(f"Sent swipe from ({start_x},{start_y}) to ({end_x},{end_y})")
        except Exception as e:
            print(f"Failed to send swipe: {e}")

    def send_enter_key(self):
        try:
            subprocess.run(['adb', 'shell', 'input', 'keyevent', '66'], timeout=5)  # KEYCODE_ENTER = 66
            print("Sent Enter key event")
        except Exception as e:
            print(f"Failed to send Enter key: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            if self.streaming:
                self.stream_timer.stop()
                self.streaming = False
                print("Streaming mode OFF due to manual refresh")
            print("Refreshing screenshot on 'r' press...")
            self.update_screenshot()
        elif event.key() == Qt.Key_S:
            if self.streaming:
                self.stream_timer.stop()
                self.streaming = False
                print("Streaming mode OFF")
            else:
                self.stream_timer.start(self.stream_interval_ms)
                self.streaming = True
                print(f"Streaming mode ON, interval: {self.stream_interval_ms} ms")
        elif event.key() == Qt.Key_L:  # Press 'L' to rotate view clockwise
            self.rotation_angle = (self.rotation_angle + 90) % 360
            print(f"Rotated view to {self.rotation_angle} degrees")
            self.update_scaled_pixmap()
            self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DongleTouchApp()
    window.show()
    sys.exit(app.exec_())
