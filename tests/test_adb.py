import subprocess
import time

def run_adb_command(command: str) -> str:
    """Runs an ADB command and returns the output."""
    full_command = f"adb {command}"
    print(f"Running: {full_command}")
    try:
        result = subprocess.run(
            full_command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e.stderr}")
        return e.stderr.strip()

def test_adb_connection():
    print("--- 1. Testing ADB Connection ---")
    devices_out = run_adb_command("devices")
    print(f"Devices output:\n{devices_out}\n")
    
    if "unauthorized" in devices_out:
        print("❌ Device is unauthorized! Please check your phone screen and click 'Allow USB Debugging'.")
        return
    elif "device" not in devices_out.split("List of devices attached")[1]:
        print("❌ No devices found. Please ensure USB debugging is enabled and the phone is connected.")
        return
        
    print("✅ Device is connected and authorized!")
    
    print("\n--- 2. Getting Device Info ---")
    model = run_adb_command("shell getprop ro.product.model")
    brand = run_adb_command("shell getprop ro.product.brand")
    android_version = run_adb_command("shell getprop ro.build.version.release")
    
    print(f"Phone Model: {brand} {model}")
    print(f"Android Version: {android_version}")
    
    print("\n--- 3. Testing Screen Size ---")
    screen_size = run_adb_command("shell wm size")
    print(f"Resolution: {screen_size}")
    
    print("\n--- 4. Taking a Screenshot (Test) ---")
    print("Taking a screenshot to /sdcard/test.png ...")
    run_adb_command("shell screencap -p /sdcard/test.png")
    print("Pulling screenshot to local directory ...")
    run_adb_command("pull /sdcard/test.png tests/adb_test_screenshot.png")
    print("✅ Screenshot saved to tests/adb_test_screenshot.png")
    
    # Cleanup
    run_adb_command("shell rm /sdcard/test.png")
    
    print("\n✅ All basic ADB tests completed successfully!")

if __name__ == "__main__":
    test_adb_connection()
