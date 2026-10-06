import subprocess
import sys
import os

def execute_stage(script_path):
    print(f"\n========================================================")
    print(f"🚀 RUNNING PIPELINE STAGE: {script_path}")
    print(f"========================================================")
    
    if not os.path.exists(script_path):
        print(f"❌ STAGE FILE NOT FOUND: {script_path}")
        return False
        
    try:
        result = subprocess.run([sys.executable, script_path], check=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
        print(f"✅ STAGE COMPLETED SUCCESSFULLY: {script_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ STAGE FAILED: {script_path}")
        if e.stderr:
            print(f"Error Details:\n{e.stderr.strip()}")
        return False

def main():
    print("🏁 INITIALIZING END-TO-END MULTI-AGENT DATA PIPELINE CORE...")
    
    if not execute_stage("pipeline_ingest.py"):
        print("\n⛔ Pipeline halted due to error in Ingestion Stage.")
        return
        
    if not execute_stage("database_layers/silver_transform.py"):
        print("\n⛔ Pipeline halted due to error in Silver Transformation Stage.")
        return
        
    if not execute_stage("database_layers/gold_transform.py"):
        print("\n⛔ Pipeline execution incomplete.")
        return
        
    print("\n========================================================")
    print("🎉 PIPELINE RUN SUCCESSFUL: Data fully loaded into Gold Schema!")
    print("========================================================")

if __name__ == "__main__":
    main()
