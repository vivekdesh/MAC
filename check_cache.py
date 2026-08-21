import json
import glob
import os
import datetime

def get_vm_name(rel_folder):
    if rel_folder.startswith("Ubentu/suresh"):
        return "Suresh VM (AWS)"
    if rel_folder.startswith("Google/"):
        bot = os.path.basename(rel_folder)
        if bot in ["mod_rsi", "sensex", "selling_1", "binance"]:
            return "Oracle VM (GCP)"
        elif bot == "whatsapp":
            return "Oracle 2 VM (GCP)"
        else:
            return "Vivek VM (GCP)"
    return "Unknown VM"

def check_cache_and_logs():
    base_dir = "/Users/vivek/ICICI_Direct"
    search_paths = [
        f"{base_dir}/Google/*", 
        f"{base_dir}/Ubentu/suresh/*"
    ]

    # Pre-define VM Order (Bandu completely removed)
    vm_order = ["Vivek VM (GCP)", "Oracle VM (GCP)", "Oracle 2 VM (GCP)", "Suresh VM (AWS)", "Unknown VM"]

    # =========================================================================
    # PARSE ALL DATA FIRST
    # =========================================================================
    
    # 1. Parse Cache Files
    files = []
    for p in search_paths:
        for f in glob.glob(p + "/parameters_cache.json"):
            if "Bandu" not in f:
                files.append(f)

    cache_data = {vm: [] for vm in vm_order}
    for f in files:
        try:
            with open(f, "r") as json_file:
                data = json.load(json_file)
                rel_folder = os.path.relpath(os.path.dirname(f), base_dir)
                vm_name = get_vm_name(rel_folder)
                
                p_stop = str(data.get("Program_stop", "N/A"))
                p_exec = str(data.get("Program_stop_Executor", "N/A"))
                
                mtime = os.path.getmtime(f)
                dt = datetime.datetime.fromtimestamp(mtime)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                if vm_name not in cache_data:
                    cache_data[vm_name] = []
                cache_data[vm_name].append((os.path.basename(rel_folder), p_stop, p_exec, time_str))
        except Exception:
            pass

    # 2. Parse Log Files
    log_files = []
    for p in search_paths:
        for f in glob.glob(p + "/*.log"):
            if "Bandu" not in f:
                log_files.append(f)
    log_files = list(set(log_files))
    
    quota_keywords = ["quota exceeded", "ratelimitexceeded", "too many requests", "[429]"]
    general_error_keywords = ["- error -", "exception", "traceback"]
    
    quota_errors = {vm: [] for vm in vm_order}
    general_errors = {vm: {} for vm in vm_order}
    today = datetime.datetime.now().date()
    
    for log_file in log_files:
        try:
            mtime = os.path.getmtime(log_file)
            file_date = datetime.datetime.fromtimestamp(mtime).date()
            if file_date != today:
                continue
                
            rel_folder = os.path.relpath(os.path.dirname(log_file), base_dir)
            vm_name = get_vm_name(rel_folder)
            bot_name = os.path.basename(rel_folder)
            
            if vm_name not in general_errors:
                general_errors[vm_name] = {}
            if bot_name not in general_errors[vm_name]:
                general_errors[vm_name][bot_name] = []
                
            if vm_name not in quota_errors:
                quota_errors[vm_name] = []
            
            with open(log_file, "r", errors="ignore") as lf:
                for line in lf:
                    lower_line = line.lower()
                    
                    is_quota = False
                    if any(kw in lower_line for kw in quota_keywords):
                        quota_errors[vm_name].append((bot_name, os.path.basename(log_file), line.strip()))
                        is_quota = True
                        
                    if not is_quota and any(kw in lower_line for kw in general_error_keywords):
                        general_errors[vm_name][bot_name].append((os.path.basename(log_file), line.strip()))
        except Exception:
            pass

    # =========================================================================
    # PRINT RESULTS IN REVERSE ORDER (3, 2, 1)
    # =========================================================================

    # =========================================================================
    # TASK 3: GENERAL ERRORS TODAY (Max 5 per bot)
    # =========================================================================
    print("\n🔎 [TASK 3] CHECKING FOR OTHER ERRORS TODAY (Excluding Quota) 🔎")
    print("=" * 95)
    
    total_general = sum(sum(len(errs) for errs in bots.values()) for bots in general_errors.values())

    if total_general == 0:
        print("✅ NO OTHER ERRORS FOUND TODAY! All bots are running smoothly.")
    else:
        print(f"⚠️ FOUND OTHER ERRORS TODAY (Showing max 7 latest per bot):")
        
        for vm in vm_order:
            vm_has_errors = sum(len(errs) for errs in general_errors.get(vm, {}).values()) > 0
            if vm_has_errors:
                print(f"\n🖥️  {vm}")
                print("=" * 95)
                
                for bot, errs in general_errors[vm].items():
                    if len(errs) > 0:
                        latest_errs = errs[-7:]
                        print(f"  [{bot}] - {len(errs)} total errors today (showing latest {len(latest_errs)}):")
                        print("  " + "-" * 93)
                        for fname, err in latest_errs:
                            if len(err) > 110:
                                err = err[:107] + "..."
                            print(f"    -> {err}")
                        print()
            
    print("=" * 95 + "\n")

    # =========================================================================
    # TASK 2: QUOTA ERRORS TODAY
    # =========================================================================
    print("🔎 [TASK 2] CHECKING FOR GOOGLE API QUOTA ERRORS TODAY 🔎")
    print("=" * 95)
    
    total_quota = sum(len(errs) for errs in quota_errors.values())
    
    if total_quota == 0:
        print("✅ NO QUOTA ERRORS FOUND TODAY! Fast Parameter system is saving API calls.")
    else:
        print(f"⚠️ FOUND {total_quota} QUOTA ERRORS TODAY:")
        for vm in vm_order:
            if quota_errors.get(vm):
                print(f"\n🖥️  {vm} ({len(quota_errors[vm])} errors)")
                print("-" * 95)
                for bot, fname, err in quota_errors[vm]:
                    if len(err) > 110:
                        err = err[:107] + "..."
                    print(f"  [{bot}] -> {err}")
            
    print("=" * 95 + "\n")

    # # =========================================================================
    # # TASK 1: CACHE STATUS
    # # =========================================================================
    # print("🚀 [TASK 1] FAST PARAMETER LIVE CACHE STATUS (Grouped by VM) 🚀")
    # print("=" * 95)
    # print("{:<25} | {:<15} | {:<15} | {:<20}".format("Bot", "Program_stop", "Executor", "Last Downloaded"))
    # print("=" * 95)

    # for vm in vm_order:
    #     if cache_data.get(vm):
    #         print(f"\n🖥️  {vm}")
    #         print("-" * 95)
    #         for bot, p_stop, p_exec, time_str in sorted(cache_data[vm]):
    #             print("{:<25} | {:<15} | {:<15} | {:<20}".format(bot, p_stop, p_exec, time_str))
            
    # print("=" * 95 + "\n")

if __name__ == "__main__":
    check_cache_and_logs()
