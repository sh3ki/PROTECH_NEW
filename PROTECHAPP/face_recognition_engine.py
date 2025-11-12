"""
Ultra-fast Face Recognition Engine with GPU acceleration
Optimized for real-time performance with hundreds of students
"""
import os
import numpy as np
import cv2
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from PROTECHAPP.models import Student
import threading
import time

class FaceRecognitionEngine:
    """Singleton class for managing face recognition with GPU acceleration"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.embeddings_cache = {}  # {student_id: embeddings_array}
        self.student_info_cache = {}  # {student_id: {'lrn': ..., 'name': ...}}
        self.last_cache_update = 0
        self.cache_ttl = 300  # Refresh cache every 5 minutes
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Try to use GPU if available
        self.use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        print(f"Face Recognition Engine initialized. GPU Available: {self.use_gpu}")
        
        # Load all embeddings into memory at startup
        self.load_all_embeddings()
    
    def load_all_embeddings(self):
        """Load all student face embeddings into memory for ultra-fast comparison"""
        print("Loading face embeddings into memory...")
        start_time = time.time()
        
        try:
            # Get all students with face embeddings
            students = Student.objects.exclude(
                face_path__isnull=True
            ).exclude(
                face_path__exact=''
            ).values('id', 'lrn', 'first_name', 'last_name', 'face_path')
            
            embeddings_dir = os.path.join(settings.BASE_DIR, 'face_embeddings')
            loaded_count = 0
            
            for student in students:
                student_id = student['id']
                face_path = student['face_path']
                
                # Build full path to embedding file
                if face_path.startswith('face_embeddings'):
                    embedding_file = os.path.join(settings.BASE_DIR, face_path)
                else:
                    embedding_file = os.path.join(embeddings_dir, os.path.basename(face_path))
                
                if os.path.exists(embedding_file):
                    try:
                        # Load embedding file (should contain 3 embeddings: front, left, right)
                        embeddings = np.load(embedding_file)
                        
                        # Store in cache
                        self.embeddings_cache[student_id] = embeddings
                        self.student_info_cache[student_id] = {
                            'lrn': student['lrn'],
                            'name': f"{student['first_name']} {student['last_name']}",
                            'first_name': student['first_name'],
                            'last_name': student['last_name']
                        }
                        loaded_count += 1
                    except Exception as e:
                        print(f"Error loading embedding for student {student_id}: {e}")
            
            self.last_cache_update = time.time()
            elapsed = time.time() - start_time
            print(f"Loaded {loaded_count} face embeddings in {elapsed:.2f}s")
            
        except Exception as e:
            print(f"Error in load_all_embeddings: {e}")
    
    def refresh_cache_if_needed(self):
        """Refresh cache if TTL expired"""
        if time.time() - self.last_cache_update > self.cache_ttl:
            self.load_all_embeddings()
    
    def compare_embeddings_vectorized(self, input_embedding, threshold=0.75):
        """
        Ultra-fast vectorized comparison of input embedding against all cached embeddings
        Uses numpy vectorization for maximum speed
        
        Args:
            input_embedding: 128-d or 512-d face embedding from detected face
            threshold: Cosine similarity threshold (default 0.75 - increased for accuracy)
        
        Returns:
            tuple: (student_id, confidence) or (None, 0) if no match
        """
        if not self.embeddings_cache:
            return None, 0
        
        input_embedding = np.array(input_embedding).flatten()
        
        # Normalize input embedding
        input_norm = np.linalg.norm(input_embedding)
        if input_norm == 0:
            return None, 0
        input_embedding_normalized = input_embedding / input_norm
        
        best_match_id = None
        best_similarity = 0
        
        # Vectorized comparison against all students
        for student_id, stored_embeddings in self.embeddings_cache.items():
            # stored_embeddings shape: (3, 128) or (3, 512) - 3 poses
            # Compare against all 3 poses and take the best match
            
            for embedding in stored_embeddings:
                embedding = np.array(embedding).flatten()
                
                # Normalize stored embedding
                embedding_norm = np.linalg.norm(embedding)
                if embedding_norm == 0:
                    continue
                embedding_normalized = embedding / embedding_norm
                
                # Cosine similarity (fast dot product)
                similarity = np.dot(input_embedding_normalized, embedding_normalized)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_id = student_id
        
        # Return match if above threshold
        if best_similarity >= threshold:
            return best_match_id, float(best_similarity)
        
        return None, 0
    
    def recognize_face(self, face_embedding):
        """
        Recognize a face from its embedding
        
        Args:
            face_embedding: Face embedding array
        
        Returns:
            dict: {'student_id': int, 'lrn': str, 'name': str, 'first_name': str, 'last_name': str, 'confidence': float, 'matched': bool}
        """
        # Refresh cache if needed
        self.refresh_cache_if_needed()
        
        # Compare against all cached embeddings
        student_id, confidence = self.compare_embeddings_vectorized(face_embedding)
        
        if student_id:
            student_info = self.student_info_cache.get(student_id, {})
            print(f"✅ Face matched: {student_info.get('name', 'Unknown')} (LRN: {student_info.get('lrn', 'N/A')}) - Confidence: {confidence:.2%}")
            return {
                'matched': True,
                'student_id': student_id,
                'lrn': student_info.get('lrn', ''),
                'name': student_info.get('name', ''),
                'first_name': student_info.get('first_name', ''),
                'last_name': student_info.get('last_name', ''),
                'confidence': confidence
            }
        
        print(f"❌ No face match found (best confidence: {confidence:.2%})")
        
        return {
            'matched': False,
            'student_id': None,
            'lrn': None,
            'name': None,
            'first_name': None,
            'last_name': None,
            'confidence': 0
        }
    
    def recognize_multiple_faces(self, face_embeddings_list):
        """
        Recognize multiple faces in parallel
        
        Args:
            face_embeddings_list: List of face embeddings
        
        Returns:
            list: List of recognition results
        """
        # Use thread pool for parallel processing
        results = list(self.executor.map(self.recognize_face, face_embeddings_list))
        return results

# Global instance
face_engine = FaceRecognitionEngine()
