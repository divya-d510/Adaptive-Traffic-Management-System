"""
Quick test script to verify your setup is ready
Run this before starting the main system
"""
import sys

def test_imports():
    """Test if all required packages are installed"""
    print("Testing required packages...\n")
    
    tests = {
        'OpenCV': 'cv2',
        'NumPy': 'numpy',
        'Flask': 'flask'
    }
    
    failed = []
    
    for name, module in tests.items():
        try:
            __import__(module)
            print(f"✅ {name} - OK")
        except ImportError:
            print(f"❌ {name} - MISSING")
            failed.append(name)
    
    return failed

def test_camera():
    """Test if camera is accessible"""
    print("\nTesting camera access...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera - OK")
            cap.release()
            return True
        else:
            print("❌ Camera - NOT ACCESSIBLE")
            print("   Try: Different camera index, check permissions, or ensure no other app is using it")
            return False
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def main():
    print("="*60)
    print("TRAFFIC MANAGEMENT SYSTEM - SETUP TEST")
    print("="*60)
    
    # Test imports
    failed_imports = test_imports()
    
    # Test camera
    camera_ok = test_camera()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if failed_imports:
        print(f"\n❌ Missing packages: {', '.join(failed_imports)}")
        print("\nTo install missing packages, run:")
        print("   pip install -r requirements.txt")
        return False
    
    if not camera_ok:
        print("\n⚠️  Camera not accessible")
        print("   The system will still run but won't detect vehicles")
        print("   You can still view the web dashboard")
    
    if not failed_imports and camera_ok:
        print("\n✅ All tests passed! You're ready to run the system.")
        print("\nTo start the system, run:")
        print("   python camera_feed_with_dashboard.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
