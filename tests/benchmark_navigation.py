"""
Navigation & Page Transition Performance Profiler (Benchmark Suite)
Instruments SmartFileOrganizerApp to measure:
1. Initial application startup time
2. Cold (first-visit) navigation duration for all 18 pages
3. Cached (repeat-visit) navigation duration for all 18 pages (including on_page_show() and Tk idle rendering)
4. Rapid 54-switch stress loop latency (avg, p95, max)
5. Memory usage before and after 54 page transitions (tracemalloc)
"""

import os
import sys
import time
import tracemalloc
import statistics

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import SmartFileOrganizerApp, PAGE_TITLES
from animation import UIBridge, FluidAnimator


ALL_PAGES = [
    'home',
    'files',
    'media',
    'ai',
    'search',
    'smart_org',
    'automation',
    'duplicates',
    'storage',
    'activity',
    'security',
    'settings',
    'qf_desktop',
    'qf_downloads',
    'qf_documents',
    'qf_pictures',
    'qf_music',
    'qf_videos',
]


def run_benchmark(label="BASELINE"):
    tracemalloc.start()
    t0_launch = time.perf_counter()
    app = SmartFileOrganizerApp(start_minimized=True)
    app.update_idletasks()
    UIBridge.drain_now()
    launch_ms = (time.perf_counter() - t0_launch) * 1000.0

    # 1. Cold navigation (first visit to each page)
    cold_times = {}
    for pid in ALL_PAGES:
        t0 = time.perf_counter()
        app.navigate_to(pid)
        app.update_idletasks()
        UIBridge.drain_now()
        cold_times[pid] = (time.perf_counter() - t0) * 1000.0

    # Let initial background threads settle briefly
    time.sleep(0.25)
    UIBridge.drain_now()
    app.update_idletasks()

    # 2. Cached navigation (second visit to each page, measuring navigate_to + on_page_show + update_idletasks)
    cached_times = {}
    for pid in ALL_PAGES:
        t0 = time.perf_counter()
        app.navigate_to(pid)
        app.update_idletasks()
        UIBridge.drain_now()
        cached_times[pid] = (time.perf_counter() - t0) * 1000.0

    # 3. Rapid multi-page switching stress test (3 full cycles = 54 switches)
    mem_before, _ = tracemalloc.get_traced_memory()
    rapid_times = []
    for _ in range(3):
        for pid in ALL_PAGES:
            t0 = time.perf_counter()
            app.navigate_to(pid)
            app.update_idletasks()
            rapid_times.append((time.perf_counter() - t0) * 1000.0)

    mem_after, mem_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Clean shutdown
    try:
        FluidAnimator.cancel_all()
        UIBridge.stop()
        app.watcher.stop()
        if app._ipc_server:
            app._ipc_server.close()
        if app.tray_icon:
            app.tray_icon.stop()
        app.destroy()
    except Exception:
        pass

    print(f"=== BENCHMARK REPORT [{label}] ===")
    print(f"Initial Launch Time: {launch_ms:.2f} ms")
    print("\n--- Cold (1st Visit) Navigation Times (ms) ---")
    for pid, ms in cold_times.items():
        print(f"  {pid:14s}: {ms:8.2f} ms")
    print(f"  Cold Avg      : {statistics.mean(cold_times.values()):8.2f} ms | Max: {max(cold_times.values()):8.2f} ms")

    print("\n--- Cached (2nd Visit) Navigation Times (ms) ---")
    for pid, ms in cached_times.items():
        print(f"  {pid:14s}: {ms:8.2f} ms")
    print(f"  Cached Avg    : {statistics.mean(cached_times.values()):8.2f} ms | Max: {max(cached_times.values()):8.2f} ms")

    sorted_rapid = sorted(rapid_times)
    p95_idx = int(len(sorted_rapid) * 0.95)
    print("\n--- Rapid 54-Page Stress Switch Summary ---")
    print(f"  Rapid Avg     : {statistics.mean(rapid_times):8.2f} ms")
    print(f"  Rapid Median  : {statistics.median(rapid_times):8.2f} ms")
    print(f"  Rapid P95     : {sorted_rapid[p95_idx]:8.2f} ms")
    print(f"  Rapid Max     : {max(rapid_times):8.2f} ms")
    print(f"  Memory Before : {mem_before / 1024:.1f} KB")
    print(f"  Memory After  : {mem_after / 1024:.1f} KB (Delta: {(mem_after - mem_before) / 1024:+.1f} KB)")
    print(f"  Memory Peak   : {mem_peak / 1024:.1f} KB")


if __name__ == "__main__":
    lbl = sys.argv[1] if len(sys.argv) > 1 else "BASELINE"
    run_benchmark(lbl)
