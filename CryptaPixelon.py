import sys
import random
import time
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QComboBox, QLineEdit, QMessageBox, QProgressBar,
    QSlider, QTabWidget, QListWidget, QListWidgetItem, QSplitter,
    QGridLayout, QFrame, QGroupBox, QCheckBox
)
from PyQt5.QtGui import QPixmap, QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import numpy as np
import os


# ============================================================================
# AI LOGIC & ANALYSIS MODULE
# ============================================================================

class ImageAnalyzer:
    """AI-powered image analysis for smart encryption"""

    @staticmethod
    def analyze_image(image_array):
        """Analyze image properties and recommend encryption method"""
        try:
            # Convert to grayscale for analysis
            if len(image_array.shape) == 3:
                gray = np.mean(image_array, axis=2)
            else:
                gray = image_array

            # Calculate entropy
            hist, _ = np.histogram(gray, bins=256)
            hist = hist / hist.sum()
            entropy = -np.sum(hist * np.log2(hist + 1e-10))

            # Calculate contrast
            contrast = np.std(gray)

            # Calculate brightness
            brightness = np.mean(gray)

            # Detect image complexity
            edges = np.gradient(gray)[0]
            edge_density = np.count_nonzero(edges > 10) / gray.size

            return {
                'entropy': float(entropy),
                'contrast': float(contrast),
                'brightness': float(brightness),
                'edge_density': float(edge_density),
                'complexity': 'high' if entropy > 6 else 'medium' if entropy > 4 else 'low'
            }

        except Exception:
            return None

    @staticmethod
    def recommend_method(analysis):
        """AI recommendation engine"""
        if analysis['complexity'] == 'high':
            return 'aes'  # AES for complex images
        elif analysis['contrast'] > 50:
            return 'xor'  # XOR for high contrast
        else:
            return 'swap'  # Swap for standard images

    @staticmethod
    def generate_smart_key(image_analysis, base_key):
        """Generate optimized key based on image properties"""
        entropy = image_analysis['entropy']
        contrast = image_analysis['contrast']

        # Combine base key with image properties
        combined = int(base_key * entropy * contrast) % 256
        return max(1, combined)


# ============================================================================
# WORKER THREAD FOR BATCH PROCESSING
# ============================================================================

class BatchProcessWorker(QThread):
    """Worker thread for non-blocking batch processing"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, files, key, method):
        super().__init__()
        self.files = files
        self.key = key
        self.method = method

    def run(self):
        try:
            output_dir = os.path.join(os.getcwd(), 'encrypted_images')
            os.makedirs(output_dir, exist_ok=True)

            for idx, file in enumerate(self.files):
                img = Image.open(file)
                encrypted = encrypt_image_from_array(np.array(img), self.key, self.method)

                base_name = os.path.basename(file)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{name}_encrypted{ext}")

                encrypted.save(output_path)

                # Emit progress
                progress = int((idx + 1) / len(self.files) * 100)
                self.progress.emit(progress)

            self.finished.emit(f'Successfully processed {len(self.files)} images in {output_dir}')
        except Exception as e:
            self.error.emit(str(e))


# ============================================================================
# ENCRYPTION/DECRYPTION FUNCTIONS
# ============================================================================

def encrypt_image_from_array(pixels, key, method):
    """Enhanced encryption with multiple methods"""
    pixels = pixels.astype(np.int16)

    if method == 'swap':
        if len(pixels.shape) == 3 and pixels.shape[2] >= 3:
            pixels[:, :, [0, 2]] = pixels[:, :, [2, 0]]
            pixels[:, :, 1] = (pixels[:, :, 1] + key) % 256
    elif method == 'xor':
        pixels = pixels ^ key
    elif method == 'shift':
        pixels = np.left_shift(pixels, key % 8) % 256
    elif method == 'aes':
        # Simplified AES-like operation using key-based rotation
        pixels = np.roll(pixels, key, axis=0)
        pixels = (pixels + key * 3) % 256
    elif method == 'steganography':
        # Hide data in least significant bits
        noise = np.random.randint(0, 2, pixels.shape)
        pixels = (pixels & 0xFE) | noise

    return Image.fromarray(np.clip(pixels, 0, 255).astype('uint8'))


def decrypt_image_from_array(pixels, key, method):
    """Enhanced decryption with multiple methods"""
    pixels = pixels.astype(np.int16)

    if method == 'swap':
        if len(pixels.shape) == 3 and pixels.shape[2] >= 3:
            pixels[:, :, [0, 2]] = pixels[:, :, [2, 0]]
            pixels[:, :, 1] = (pixels[:, :, 1] - key) % 256
    elif method == 'xor':
        pixels = pixels ^ key
    elif method == 'shift':
        pixels = np.right_shift(pixels, key % 8) % 256
    elif method == 'aes':
        pixels = np.roll(pixels, -key, axis=0)
        pixels = (pixels - key * 3) % 256
    elif method == 'steganography':
        # Extract from LSBs - simplified recovery
        pixels = pixels & 0xFE

    return Image.fromarray(np.clip(pixels, 0, 255).astype('uint8'))


# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class CryptaPixelonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.result_image = None
        self.history = []
        self.history_index = -1
        self.theme = 'dark'
        self.batch_worker = None
        self.processing_time = 0

        self.initUI()
        self.setWindowIcon(self.create_app_icon())

    def initUI(self):
        """Initialize the UI with responsive design"""
        self.setWindowTitle('CryptaPixelon - Advanced AI Edition')
        self.setGeometry(100, 100, 1400, 900)

        # Apply theme
        self.apply_theme()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Left Panel - Image Upload & Preview
        left_panel = self.create_left_panel()

        # Center Panel - Controls & Analysis
        center_panel = self.create_center_panel()

        # Right Panel - Results & History
        right_panel = self.create_right_panel()

        # Add panels with splitter for responsive design
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet("color: #32b8c6; font-weight: bold;")

    def create_left_panel(self):
        """Create left panel with image upload and preview"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Header
        title = QLabel('📸 Image Source')
        title.setFont(QFont('Courier New', 12, QFont.Bold))
        layout.addWidget(title)

        # Upload button
        self.upload_btn = QPushButton('📁 Upload Image')
        self.upload_btn.setMinimumHeight(50)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_btn)

        # Image preview
        self.upload_label = QLabel('Drop image here\nor click upload')
        self.upload_label.setAlignment(Qt.AlignCenter)
        self.upload_label.setMinimumSize(300, 250)
        self.upload_label.setStyleSheet(self.get_preview_style())
        self.upload_label.setAcceptDrops(True)
        self.upload_label.dragEnterEvent = self.drag_enter_event
        self.upload_label.dropEvent = self.drop_event
        layout.addWidget(self.upload_label)

        # Image info display
        self.image_info = QLabel('No image loaded')
        self.image_info.setFont(QFont('Courier New', 9))
        self.image_info.setWordWrap(True)
        layout.addWidget(self.image_info)

        # AI Analysis results
        self.analysis_group = QGroupBox('🤖 AI Analysis')
        analysis_layout = QVBoxLayout()
        self.analysis_text = QLabel('Upload image for analysis')
        self.analysis_text.setFont(QFont('Courier New', 9))
        self.analysis_text.setWordWrap(True)
        analysis_layout.addWidget(self.analysis_text)
        self.analysis_group.setLayout(analysis_layout)
        layout.addWidget(self.analysis_group)

        layout.addStretch()
        panel.setStyleSheet(self.get_panel_style())
        return panel

    def create_center_panel(self):
        """Create center panel with controls"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        # Tab widget for different control sections
        tabs = QTabWidget()
        tabs.setStyleSheet(self.get_tab_style())

        # Tab 1: Encryption Controls
        encrypt_tab = self.create_encryption_tab()
        tabs.addTab(encrypt_tab, '🔐 Encryption')

        # Tab 2: Batch Processing
        batch_tab = self.create_batch_tab()
        tabs.addTab(batch_tab, '⚡ Batch')

        # Tab 3: Advanced Settings
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, '⚙️ Advanced')

        layout.addWidget(tabs)

        # Bottom action buttons
        button_layout = QGridLayout()
        button_layout.setSpacing(10)

        self.undo_btn = QPushButton('↶ Undo')
        self.undo_btn.clicked.connect(self.undo)
        button_layout.addWidget(self.undo_btn, 0, 0)

        self.redo_btn = QPushButton('↷ Redo')
        self.redo_btn.clicked.connect(self.redo)
        button_layout.addWidget(self.redo_btn, 0, 1)

        self.clear_btn = QPushButton('🗑️ Clear All')
        self.clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_btn, 1, 0, 1, 2)

        layout.addLayout(button_layout)

        # Theme toggle
        self.theme_btn = QPushButton('🌙 Dark Mode')
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        panel.setStyleSheet(self.get_panel_style())
        return panel

    def create_encryption_tab(self):
        """Create encryption controls tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Method selection
        method_label = QLabel('Encryption Method:')
        method_label.setFont(QFont('Courier New', 10, QFont.Bold))
        layout.addWidget(method_label)

        self.method_combo = QComboBox()
        self.method_combo.addItems(['swap', 'xor', 'shift', 'aes', 'steganography'])
        self.method_combo.setMinimumHeight(35)
        self.method_combo.currentTextChanged.connect(self.on_method_changed)
        layout.addWidget(self.method_combo)

        # Smart recommendation
        self.recommend_btn = QPushButton('🤖 AI Recommend Method')
        self.recommend_btn.clicked.connect(self.recommend_method)
        layout.addWidget(self.recommend_btn)

        # Key input
        key_label = QLabel('Encryption Key:')
        key_label.setFont(QFont('Courier New', 10, QFont.Bold))
        layout.addWidget(key_label)

        key_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText('Enter key (1-255)')
        self.key_input.setMinimumHeight(35)
        self.key_input.textChanged.connect(self.update_key_strength)
        key_layout.addWidget(self.key_input)

        self.smart_key_btn = QPushButton('🎲')
        self.smart_key_btn.setMaximumWidth(50)
        self.smart_key_btn.clicked.connect(self.generate_smart_key)
        self.smart_key_btn.setToolTip('Generate AI-optimized key')
        key_layout.addWidget(self.smart_key_btn)

        layout.addLayout(key_layout)

        # Key strength indicator
        self.key_strength = QLabel('Key Strength: -')
        self.key_strength.setFont(QFont('Courier New', 9))
        layout.addWidget(self.key_strength)

        # Processing info (also used for slider value text)
        self.processing_info = QLabel('')
        self.processing_info.setFont(QFont('Courier New', 9))
        layout.addWidget(self.processing_info)

        # Main action buttons
        button_layout = QGridLayout()
        button_layout.setSpacing(10)

        self.encrypt_btn = QPushButton('🔒 Encrypt Image')
        self.encrypt_btn.setMinimumHeight(45)
        self.encrypt_btn.clicked.connect(self.encrypt)
        button_layout.addWidget(self.encrypt_btn, 0, 0)

        self.decrypt_btn = QPushButton('🔓 Decrypt Image')
        self.decrypt_btn.setMinimumHeight(45)
        self.decrypt_btn.clicked.connect(self.decrypt)
        button_layout.addWidget(self.decrypt_btn, 0, 1)

        layout.addLayout(button_layout)
        layout.addStretch()

        return widget

    def create_batch_tab(self):
        """Create batch processing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        title = QLabel('⚡ Batch Processing')
        title.setFont(QFont('Courier New', 11, QFont.Bold))
        layout.addWidget(title)

        info = QLabel('Process multiple images at once with same settings')
        info.setFont(QFont('Courier New', 9))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.batch_btn = QPushButton('📂 Select Multiple Images')
        self.batch_btn.setMinimumHeight(40)
        self.batch_btn.clicked.connect(self.batch_process)
        layout.addWidget(self.batch_btn)

        # Progress bar
        self.batch_progress = QProgressBar()
        self.batch_progress.setValue(0)
        self.batch_progress.setVisible(False)
        layout.addWidget(self.batch_progress)

        # Batch info
        self.batch_info = QLabel('No batch operation running')
        self.batch_info.setFont(QFont('Courier New', 9))
        self.batch_info.setWordWrap(True)
        layout.addWidget(self.batch_info)

        layout.addStretch()
        return widget

    def create_advanced_tab(self):
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Encryption strength slider
        strength_label = QLabel('Encryption Strength:')
        strength_label.setFont(QFont('Courier New', 10, QFont.Bold))
        layout.addWidget(strength_label)

        self.strength_slider = QSlider(Qt.Horizontal)
        self.strength_slider.setMinimum(1)
        self.strength_slider.setMaximum(10)
        self.strength_slider.setValue(5)
        self.strength_slider.setTickPosition(QSlider.TicksBelow)
        layout.addWidget(self.strength_slider)

        # UX TIP: show live strength value
        self.strength_slider.valueChanged.connect(self.update_strength_label)

        # Quality preservation
        quality_label = QLabel('Output Quality:')
        quality_label.setFont(QFont('Courier New', 10, QFont.Bold))
        layout.addWidget(quality_label)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(50)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(90)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        layout.addWidget(self.quality_slider)

        # UX TIP: show live quality value
        self.quality_slider.valueChanged.connect(self.update_quality_label)

        # Additional options
        self.add_noise_check = QCheckBox('Add protective noise')
        layout.addWidget(self.add_noise_check)

        self.compress_check = QCheckBox('Compress output')
        layout.addWidget(self.compress_check)

        # Export options
        export_label = QLabel('Export Settings:')
        export_label.setFont(QFont('Courier New', 10, QFont.Bold))
        layout.addWidget(export_label)

        export_layout = QGridLayout()

        self.save_btn = QPushButton('💾 Save Image')
        self.save_btn.clicked.connect(self.save_image)
        export_layout.addWidget(self.save_btn, 0, 0)

        self.save_report_btn = QPushButton('📄 Save Report')
        self.save_report_btn.clicked.connect(self.export_report)
        export_layout.addWidget(self.save_report_btn, 0, 1)

        self.log_btn = QPushButton('📋 Export Log')
        self.log_btn.clicked.connect(self.export_log)
        export_layout.addWidget(self.log_btn, 1, 0, 1, 2)

        layout.addLayout(export_layout)
        layout.addStretch()

        # initialize labels once
        self.update_strength_label(self.strength_slider.value())
        self.update_quality_label(self.quality_slider.value())

        return widget

    def create_right_panel(self):
        """Create right panel with results and history"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Results section
        title = QLabel('🎨 Results')
        title.setFont(QFont('Courier New', 12, QFont.Bold))
        layout.addWidget(title)

        self.result_label = QLabel('Result will appear here')
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumSize(300, 250)
        self.result_label.setStyleSheet(self.get_preview_style())
        layout.addWidget(self.result_label)

        # Comparison metrics
        self.metrics_group = QGroupBox('📊 Metrics')
        metrics_layout = QVBoxLayout()
        self.metrics_text = QLabel('Metrics will appear after processing')
        self.metrics_text.setFont(QFont('Courier New', 8))
        self.metrics_text.setWordWrap(True)
        metrics_layout.addWidget(self.metrics_text)
        self.metrics_group.setLayout(metrics_layout)
        layout.addWidget(self.metrics_group)

        # History panel
        history_title = QLabel('📜 Operation History')
        history_title.setFont(QFont('Courier New', 10, QFont.Bold))
        layout.addWidget(history_title)

        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(150)
        self.history_list.itemClicked.connect(self.on_history_click)
        layout.addWidget(self.history_list)

        panel.setStyleSheet(self.get_panel_style())
        return panel

    # ========================= CORE FUNCTIONALITY ==========================

    def upload_image(self):
        """Handle image upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Select Image', '', 'Images (*.png *.jpg *.jpeg *.bmp)'
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, path):
        """Load and display image"""
        try:
            self.current_image = Image.open(path)

            # Display preview
            pixmap = QPixmap(path).scaled(300, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.upload_label.setPixmap(pixmap)

            # Show image info
            size = os.path.getsize(path) / 1024
            self.image_info.setText(
                f"📁 {os.path.basename(path)}\n"
                f"📐 {self.current_image.size[0]}×{self.current_image.size[1]}px\n"
                f"💾 {size:.1f}KB"
            )

            # Run AI analysis
            self.analyze_image()

            self.statusBar().showMessage(f'✓ Image loaded: {os.path.basename(path)}')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load image: {str(e)}')

    def analyze_image(self):
        """Run AI analysis on current image"""
        try:
            image_array = np.array(self.current_image)
            analysis = ImageAnalyzer.analyze_image(image_array)

            if analysis:
                recommended = ImageAnalyzer.recommend_method(analysis)

                self.analysis_text.setText(
                    f"Entropy: {analysis['entropy']:.2f}\n"
                    f"Contrast: {analysis['contrast']:.1f}\n"
                    f"Complexity: {analysis['complexity']}\n"
                    f"🤖 Recommended: {recommended.upper()}"
                )
        except Exception as e:
            self.analysis_text.setText(f'Analysis failed: {str(e)}')

    def recommend_method(self):
        """Apply AI recommended encryption method"""
        if not self.current_image:
            QMessageBox.warning(self, 'No Image', 'Please upload an image first.')
            return

        try:
            image_array = np.array(self.current_image)
            analysis = ImageAnalyzer.analyze_image(image_array)
            recommended = ImageAnalyzer.recommend_method(analysis)

            self.method_combo.setCurrentText(recommended)
            QMessageBox.information(
                self, 'Recommendation',
                f'AI recommends: {recommended.upper()}\n\n'
                f'Image Complexity: {analysis["complexity"]}'
            )
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Analysis failed: {str(e)}')

    def generate_smart_key(self):
        """Generate AI-optimized encryption key"""
        if not self.current_image:
            QMessageBox.warning(self, 'No Image', 'Please upload an image first.')
            return

        try:
            image_array = np.array(self.current_image)
            analysis = ImageAnalyzer.analyze_image(image_array)
            base_key = random.randint(1, 255)
            smart_key = ImageAnalyzer.generate_smart_key(analysis, base_key)

            self.key_input.setText(str(smart_key))

            QMessageBox.information(
                self, 'Smart Key Generated',
                f'AI-optimized key: {smart_key}\n\n'
                f'Based on image entropy and contrast analysis'
            )
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Key generation failed: {str(e)}')

    def update_key_strength(self):
        """Update key strength indicator"""
        try:
            key = int(self.key_input.text())
            if 1 <= key <= 255:
                strength = min(10, key // 25 + 1)
                bar = '█' * strength + '░' * (10 - strength)
                self.key_strength.setText(f'Key Strength: {bar} ({key}/255)')
        except Exception:
            self.key_strength.setText('Key Strength: Invalid')

    def on_method_changed(self):
        """Handle method change"""
        method = self.method_combo.currentText()
        descriptions = {
            'swap': 'Fast, simple channel swapping',
            'xor': 'Mathematical XOR operation',
            'shift': 'Bit shifting encryption',
            'aes': 'Advanced encryption standard',
            'steganography': 'Hide data in LSBs'
        }
        self.processing_info.setText(f'Method: {descriptions.get(method, "")}')

    def encrypt(self):
        """Encrypt the image"""
        if not self.current_image:
            QMessageBox.warning(self, 'No Image', 'Please upload an image first.')
            return

        try:
            key = int(self.key_input.text())
            if not (1 <= key <= 255):
                raise ValueError('Key must be between 1 and 255.')
        except ValueError as e:
            QMessageBox.warning(self, 'Invalid Key', f'Please enter a valid key.\n{str(e)}')
            return

        method = self.method_combo.currentText()

        try:
            start_time = time.time()

            # Save to history
            self.history.append({
                'image': self.current_image.copy(),
                'operation': 'original'
            })

            # Encrypt
            self.result_image = encrypt_image_from_array(np.array(self.current_image), key, method)

            self.processing_time = time.time() - start_time

            # Display result
            self.display_result()

            # Update history
            self.add_history_item(f'Encrypted with {method}', self.result_image)

            # Update metrics
            self.update_metrics()

            self.statusBar().showMessage(f'✓ Encryption completed in {self.processing_time:.3f}s')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Encryption failed: {str(e)}')

    def decrypt(self):
        """Decrypt the image"""
        if not self.result_image and self.current_image:
           self.result_image = self.current_image.copy()
        
        if not self.result_image:
            QMessageBox.warning(self, 'No Result', 'Please encrypt an image first.')
            return

        try:
            key = int(self.key_input.text())
            if not (1 <= key <= 255):
                raise ValueError('Key must be between 1 and 255.')
        except ValueError as e:
            QMessageBox.warning(self, 'Invalid Key', f'Please enter a valid key.\n{str(e)}')
            return

        method = self.method_combo.currentText()

        try:
            start_time = time.time()

            # Save to history
            self.history.append({
                'image': self.result_image.copy(),
                'operation': f'encrypted_{method}'
            })

            # Decrypt
            self.result_image = decrypt_image_from_array(np.array(self.result_image), key, method)

            self.processing_time = time.time() - start_time

            # Display result
            self.display_result()

            # Update history
            self.add_history_item(f'Decrypted with {method}', self.result_image)

            # Update metrics
            self.update_metrics()

            self.statusBar().showMessage(f'✓ Decryption completed in {self.processing_time:.3f}s')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Decryption failed: {str(e)}')

    def batch_process(self):
        """Handle batch processing with progress"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 'Select Images', '', 'Images (*.png *.jpg *.jpeg *.bmp)'
        )

        if not files:
            return

        try:
            key = int(self.key_input.text())
            if not (1 <= key <= 255):
                raise ValueError('Key must be between 1 and 255.')
        except ValueError as e:
            QMessageBox.warning(self, 'Invalid Key', f'Please enter a valid key.\n{str(e)}')
            return

        method = self.method_combo.currentText()

        # Show progress bar
        self.batch_progress.setVisible(True)
        self.batch_progress.setValue(0)
        self.batch_info.setText(f'Processing {len(files)} images...')

        # Start worker thread
        self.batch_worker = BatchProcessWorker(files, key, method)
        self.batch_worker.progress.connect(self.update_batch_progress)
        self.batch_worker.finished.connect(self.on_batch_finished)
        self.batch_worker.error.connect(self.on_batch_error)
        self.batch_worker.start()

    def update_batch_progress(self, value):
        """Update batch progress bar"""
        self.batch_progress.setValue(value)

    def on_batch_finished(self, message):
        """Handle batch completion"""
        self.batch_progress.setVisible(False)
        self.batch_info.setText(message)
        QMessageBox.information(self, 'Batch Complete', message)
        self.statusBar().showMessage('✓ Batch processing complete')

    def on_batch_error(self, error):
        """Handle batch error"""
        self.batch_progress.setVisible(False)
        self.batch_info.setText(f'Error: {error}')
        QMessageBox.critical(self, 'Batch Error', error)

    def display_result(self):
        """Display result image"""
        temp_path = '/tmp/result.png'
        self.result_image.save(temp_path)
        pixmap = QPixmap(temp_path).scaled(300, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.result_label.setPixmap(pixmap)

    def update_metrics(self):
        """Calculate and display metrics"""
        try:
            if self.current_image and self.result_image:
                orig_array = np.array(self.current_image).flatten()
                result_array = np.array(self.result_image).flatten()

                # MSE
                mse = np.mean((orig_array - result_array) ** 2)

                # Entropy difference
                orig_hist, _ = np.histogram(orig_array, bins=256)
                result_hist, _ = np.histogram(result_array, bins=256)

                orig_hist = orig_hist / orig_hist.sum()
                result_hist = result_hist / result_hist.sum()

                orig_entropy = -np.sum(orig_hist * np.log2(orig_hist + 1e-10))
                result_entropy = -np.sum(result_hist * np.log2(result_hist + 1e-10))

                self.metrics_text.setText(
                    f"⏱️ Processing Time: {self.processing_time:.3f}s\n"
                    f"📊 Mean Squared Error: {mse:.1f}\n"
                    f"🔢 Entropy Increase: {result_entropy - orig_entropy:.2f}\n"
                    f"💾 Original: {self.current_image.size[0]}×{self.current_image.size[1]}\n"
                    f"🎨 Result: {self.result_image.size[0]}×{self.result_image.size[1]}"
                )
        except Exception as e:
            self.metrics_text.setText(f'Metrics error: {str(e)}')

    def add_history_item(self, operation, image):
        """Add item to operation history"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        item_text = f'{timestamp} - {operation}'

        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, image)
        self.history_list.insertItem(0, item)

        # Limit history to 10 items
        if self.history_list.count() > 10:
            self.history_list.takeItem(self.history_list.count() - 1)

    def on_history_click(self, item):
        """Restore image from history"""
        image = item.data(Qt.UserRole)
        if isinstance(image, Image.Image):
            self.result_image = image
            self.display_result()
            self.statusBar().showMessage('✓ Restored from history')

    def undo(self):
        """Undo last operation"""
        if self.history:
            self.history.pop()
            if self.history:
                self.result_image = Image.fromarray(np.array(self.history[-1]['image']))
                self.display_result()
                self.statusBar().showMessage('✓ Undo complete')
        else:
            QMessageBox.information(self, 'Undo', 'No operations to undo.')

    def redo(self):
        """Redo last operation"""
        QMessageBox.information(self, 'Redo', 'Redo not implemented yet.')

    def clear_all(self):
        """Clear all data"""
        reply = QMessageBox.question(
            self, 'Clear All',
            'Are you sure you want to clear all data?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.current_image = None
            self.result_image = None
            self.history = []
            self.upload_label.setPixmap(QPixmap())
            self.upload_label.setText('Drop image here\nor click upload')
            self.result_label.setPixmap(QPixmap())
            self.result_label.setText('Result will appear here')
            self.key_input.clear()
            self.method_combo.setCurrentIndex(0)
            self.history_list.clear()
            self.metrics_text.setText('Metrics will appear after processing')
            self.analysis_text.setText('Upload image for analysis')
            self.image_info.setText('No image loaded')
            self.statusBar().showMessage('✓ All data cleared')

    def save_image(self):
        """Save result image"""
        if not self.result_image:
            QMessageBox.warning(self, 'No Image', 'No result image to save.')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Image', '',
            'PNG Image (*.png);;JPG Image (*.jpg);;All Files (*.*)'
        )

        if file_path:
            try:
                self.result_image.save(file_path)
                QMessageBox.information(self, 'Saved', f'Image saved successfully!\n{file_path}')
                self.statusBar().showMessage(f'✓ Image saved: {os.path.basename(file_path)}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save: {str(e)}')

    def export_report(self):
        """Export detailed encryption report"""
        if not self.result_image:
            QMessageBox.warning(self, 'No Data', 'Please process an image first.')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Report', '', 'Text File (*.txt)'
        )

        if file_path:
            try:
                report = f"""
╔══════════════════════════════════════════════════════════════╗
║           PIXEL ENCRYPTOR - ENCRYPTION REPORT              ║
╚══════════════════════════════════════════════════════════════╝

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[IMAGE INFORMATION]
Original Size: {self.current_image.size if self.current_image else 'N/A'}
Result Size: {self.result_image.size if self.result_image else 'N/A'}
Format: {self.result_image.format if self.result_image else 'N/A'}

[ENCRYPTION SETTINGS]
Method: {self.method_combo.currentText()}
Key: {self.key_input.text()}
Strength Level: {self.strength_slider.value()}/10
Quality: {self.quality_slider.value()}%

[PROCESSING METRICS]
Processing Time: {self.processing_time:.3f} seconds
Encryption Strength: {self.strength_slider.value() * 10}%

[ANALYSIS DATA]
{self.analysis_text.text()}

[EXPORT OPTIONS]
Noise Protected: {'Yes' if self.add_noise_check.isChecked() else 'No'}
Compressed: {'Yes' if self.compress_check.isChecked() else 'No'}

═══════════════════════════════════════════════════════════════
Generated by CryptaPixelon - Advanced AI Edition
"""
                with open(file_path, 'w') as f:
                    f.write(report)

                QMessageBox.information(self, 'Saved', f'Report saved successfully!\n{file_path}')
                self.statusBar().showMessage('✓ Report exported')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save report: {str(e)}')

    def export_log(self):
        """Export operation log"""
        if self.history_list.count() == 0:
            QMessageBox.warning(self, 'No History', 'No operations to export.')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Log', '', 'Log File (*.log);;Text File (*.txt)'
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write('PIXEL ENCRYPTOR - OPERATION LOG\n')
                    f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                    f.write('=' * 50 + '\n\n')

                    for i in range(self.history_list.count()):
                        item = self.history_list.item(i)
                        f.write(f'{i+1}. {item.text()}\n')

                QMessageBox.information(self, 'Saved', f'Log exported successfully!\n{file_path}')
                self.statusBar().showMessage('✓ Log exported')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to export log: {str(e)}')

    def drag_enter_event(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self, event):
        """Handle file drop"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.load_image(file_path)
            else:
                QMessageBox.warning(self, 'Invalid File', 'Please drop a valid image file.')

    # ============================== THEME / STYLE ===========================

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        self.apply_theme()
        self.theme_btn.setText('☀️ Light Mode' if self.theme == 'dark' else '🌙 Dark Mode')

    def apply_theme(self):
        """Apply current theme"""
        if self.theme == 'dark':
            dark_stylesheet = """
                QMainWindow, QWidget, QFrame { background: #0f1419; color: #ffffff; }
                QLabel { color: #ffffff; }

                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #1a3a5c, stop:1 #0f2438);
                    color: #ffffff;
                    border: 2px solid #32b8c6;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #32b8c6, stop:1 #1a3a5c);
                }

                QLineEdit, QComboBox, QSpinBox {
                    background: #1a2635;
                    color: #ffffff;
                    border: 1px solid #32b8c6;
                    border-radius: 5px;
                    padding: 5px;
                }

                QProgressBar { border: 1px solid #32b8c6; background: #1a2635; }
                QProgressBar::chunk { background: #32b8c6; }

                QTabWidget::pane { border: 1px solid #32b8c6; }
                QTabBar::tab { background: #1a2635; color: #ffffff; padding: 5px 20px; }
                QTabBar::tab:selected { background: #32b8c6; }

                QGroupBox {
                    color: #32b8c6;
                    border: 1px solid #32b8c6;
                    border-radius: 5px;
                    padding: 10px;
                }

                QListWidget {
                    background: #1a2635;
                    color: #ffffff;
                    border: 1px solid #32b8c6;
                }

                QScrollBar:vertical { background: #1a2635; }
                QScrollBar::handle:vertical { background: #32b8c6; border-radius: 5px; }

                /* 🔹 SLIDERS – DARK MODE */
                QSlider::groove:horizontal {
                    border: 1px solid #32b8c6;
                    height: 8px;
                    background: #101b29;
                    border-radius: 4px;
                }
                QSlider::sub-page:horizontal {
                    background: #32b8c6;
                    border: 1px solid #32b8c6;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::add-page:horizontal {
                    background: #06101f;
                    border: 1px solid #0b2030;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #ffffff;
                    border: 2px solid #32b8c6;
                    width: 18px;
                    margin: -6px 0;
                    border-radius: 9px;
                }
                QSlider::handle:horizontal:hover {
                    background: #32b8c6;
                    border: 2px solid #ffffff;
                }
            """
            self.setStyleSheet(dark_stylesheet)
        else:
            light_stylesheet = """
                QMainWindow, QWidget, QFrame { background: #f5f7fa; color: #111111; }
                QLabel { color: #00ffff; }

                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #e3f2fd, stop:1 #bbdefb);
                    color: #0d47a1;
                    border: 2px solid #1976d2;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #1976d2, stop:1 #1565c0);
                    color: #ffffff;
                }

                QLineEdit, QComboBox, QSpinBox {
                    background: #ffffff;
                    color: #08B305;
                    border: 1px solid #1976d2;
                    border-radius: 5px;
                    padding: 5px;
                }

                QListWidget {
                    background: #ffffff;
                    color: #FF2800;
                    border: 1px solid #1976d2;
                }

                QGroupBox {
                    color: #0d47a1;
                    border: 1px solid #1976d2;
                    border-radius: 5px;
                    padding: 10px;
                }

                /* 🔹 SLIDERS – LIGHT MODE */
                QSlider::groove:horizontal {
                    border: 1px solid #1976d2;
                    height: 8px;
                    background: #e3f2fd;
                    border-radius: 4px;
                }
                QSlider::sub-page:horizontal {
                    background: #1976d2;
                    border: 1px solid #1976d2;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::add-page:horizontal {
                    background: #cfd8dc;
                    border: 1px solid #b0bec5;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #ffffff;
                    border: 2px solid #1976d2;
                    width: 18px;
                    margin: -6px 0;
                    border-radius: 9px;
                }
                QSlider::handle:horizontal:hover {
                    background: #1976d2;
                    border: 2px solid #ffffff;
                }
            """
            self.setStyleSheet(light_stylesheet)

    def get_panel_style(self):
        """Get panel styling"""
        if self.theme == 'dark':
            return """
                QFrame {
                    background: #1a2635;
                    border: 2px solid #32b8c6;
                    border-radius: 10px;
                    padding: 10px;
                }
            """
        else:
            return """
                QFrame {
                    background: #ffffff;
                    border: 2px solid #1976d2;
                    border-radius: 10px;
                    padding: 10px;
                }
            """

    def get_preview_style(self):
        """Get preview label styling"""
        if self.theme == 'dark':
            return """
                QLabel {
                    background: #0f1419;
                    border: 2px dashed #32b8c6;
                    border-radius: 8px;
                    color: #32b8c6;
                }
            """
        else:
            return """
                QLabel {
                    background: #102027;
                    border: 2px dashed #1976d2;
                    border-radius: 8px;
                    color: #80d8ff;
                }
            """

    def get_tab_style(self):
        """Get tab widget styling"""
        return ""

    def create_app_icon(self):
        """Create application icon"""
        icon = QPixmap(64, 64)
        icon.fill(QColor(50, 184, 198, 0))
        return QIcon(icon)

    # =============== UX helper: slider value labels ===================

    def update_strength_label(self, value):
        """Show live encryption strength value"""
        self.processing_info.setText(
            f"Encryption Strength: {value}/10 | Output Quality: {self.quality_slider.value()}%"
        )

    def update_quality_label(self, value):
        """Show live output quality value"""
        self.processing_info.setText(
            f"Encryption Strength: {self.strength_slider.value()}/10 | Output Quality: {value}%"
        )


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CryptaPixelonApp()
    window.show()
    sys.exit(app.exec_())
