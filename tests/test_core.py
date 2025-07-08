import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
import sys
import zipfile
import tarfile

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from radarr_extractor.core import (
    is_compressed_file, 
    is_temp_directory, 
    extract_archive,
    process_file
)


class TestCore(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_is_compressed_file(self):
        """Test compressed file detection."""
        # Test positive cases
        self.assertTrue(is_compressed_file("test.rar"))
        self.assertTrue(is_compressed_file("test.zip"))
        self.assertTrue(is_compressed_file("test.7z"))
        self.assertTrue(is_compressed_file("test.tar.gz"))
        self.assertTrue(is_compressed_file("test.tar.bz2"))
        self.assertTrue(is_compressed_file("test.tar"))
        self.assertTrue(is_compressed_file("test.tgz"))
        self.assertTrue(is_compressed_file("test.tbz2"))
        
        # Test case insensitive
        self.assertTrue(is_compressed_file("TEST.RAR"))
        self.assertTrue(is_compressed_file("Test.Zip"))
        
        # Test negative cases
        self.assertFalse(is_compressed_file("test.txt"))
        self.assertFalse(is_compressed_file("test.mp4"))
        self.assertFalse(is_compressed_file("test.mkv"))
        self.assertFalse(is_compressed_file("test"))
    
    def test_is_temp_directory(self):
        """Test temporary directory detection."""
        # Test positive cases
        self.assertTrue(is_temp_directory("/downloads/temp/file.rar"))
        self.assertTrue(is_temp_directory("/downloads/tmp/file.zip"))
        self.assertTrue(is_temp_directory("/some/path/temp/file.7z"))
        self.assertTrue(is_temp_directory("/some/path/tmp/file.tar.gz"))
        
        # Test case insensitive
        self.assertTrue(is_temp_directory("/downloads/TEMP/file.rar"))
        self.assertTrue(is_temp_directory("/downloads/TMP/file.zip"))
        
        # Test negative cases
        self.assertFalse(is_temp_directory("/downloads/movies/file.rar"))
        self.assertFalse(is_temp_directory("/downloads/completed/file.zip"))
        self.assertFalse(is_temp_directory("/downloads/file.7z"))
    
    def test_extract_archive_zip(self):
        """Test ZIP archive extraction."""
        # Create a test ZIP file
        test_zip = os.path.join(self.temp_dir, "test.zip")
        test_content = "This is test content"
        
        with zipfile.ZipFile(test_zip, 'w') as zf:
            zf.writestr("test.txt", test_content)
        
        # Mock the EXTRACTED_DIR
        with patch('radarr_extractor.core.EXTRACTED_DIR', self.temp_dir):
            extract_dir = extract_archive(test_zip)
            
            # Check that extraction was successful
            self.assertTrue(os.path.exists(extract_dir))
            extracted_file = os.path.join(extract_dir, "test.txt")
            self.assertTrue(os.path.exists(extracted_file))
            
            # Check file content
            with open(extracted_file, 'r') as f:
                self.assertEqual(f.read(), test_content)
    
    def test_extract_archive_tar_gz(self):
        """Test TAR.GZ archive extraction."""
        # Create a test TAR.GZ file
        test_tar = os.path.join(self.temp_dir, "test.tar.gz")
        test_content = "This is test content"
        
        # Create a temporary file to add to the archive
        temp_file = os.path.join(self.temp_dir, "temp_test.txt")
        with open(temp_file, 'w') as f:
            f.write(test_content)
        
        with tarfile.open(test_tar, 'w:gz') as tf:
            tf.add(temp_file, arcname="test.txt")
        
        # Mock the EXTRACTED_DIR
        with patch('radarr_extractor.core.EXTRACTED_DIR', self.temp_dir):
            extract_dir = extract_archive(test_tar)
            
            # Check that extraction was successful
            self.assertTrue(os.path.exists(extract_dir))
            extracted_file = os.path.join(extract_dir, "test.txt")
            self.assertTrue(os.path.exists(extracted_file))
            
            # Check file content
            with open(extracted_file, 'r') as f:
                self.assertEqual(f.read(), test_content)
    
    def test_extract_archive_unsupported(self):
        """Test unsupported archive format."""
        test_file = os.path.join(self.temp_dir, "test.unsupported")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with patch('radarr_extractor.core.EXTRACTED_DIR', self.temp_dir):
            with self.assertRaises(Exception) as context:
                extract_archive(test_file)
            
            self.assertIn("Unsupported archive format", str(context.exception))
    
    @patch('radarr_extractor.core.is_file_extracted')
    @patch('radarr_extractor.core.extract_archive')
    @patch('radarr_extractor.core.record_extracted_file')
    @patch('radarr_extractor.core.notify_radarr')
    def test_process_file_success(self, mock_notify, mock_record, mock_extract, mock_is_extracted):
        """Test successful file processing."""
        # Setup mocks
        mock_is_extracted.return_value = False
        mock_extract.return_value = "/extracted/path"
        
        test_file = "/downloads/test.rar"
        
        # Process the file
        process_file(test_file)
        
        # Verify calls
        mock_is_extracted.assert_called_once_with(test_file)
        mock_extract.assert_called_once_with(test_file)
        mock_record.assert_called_once_with(test_file)
        mock_notify.assert_called_once_with("/extracted/path")
    
    @patch('radarr_extractor.core.is_file_extracted')
    def test_process_file_already_extracted(self, mock_is_extracted):
        """Test processing file that was already extracted."""
        mock_is_extracted.return_value = True
        
        test_file = "/downloads/test.rar"
        
        # Process the file
        process_file(test_file)
        
        # Verify only is_file_extracted was called
        mock_is_extracted.assert_called_once_with(test_file)
    
    def test_process_file_non_compressed(self):
        """Test processing non-compressed file."""
        test_file = "/downloads/test.txt"
        
        # Process the file (should do nothing)
        process_file(test_file)
        
        # Test passes if no exception is raised
        self.assertTrue(True)
    
    def test_process_file_temp_directory(self):
        """Test processing file in temp directory."""
        test_file = "/downloads/temp/test.rar"
        
        # Process the file (should be skipped)
        process_file(test_file)
        
        # Test passes if no exception is raised
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
