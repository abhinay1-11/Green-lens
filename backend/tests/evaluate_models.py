import os
import sys
import time

# Ensure UTF-8 output encoding for console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.identification.factory import get_identification_provider
from app.utils.image_validation import validate_image_file

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images"))

def run_model_evaluation():
    print("==========================================================")
    print("BIODIVERSITY IDENTIFICATION MODEL EVALUATION BENCHMARK")
    print("==========================================================")

    categories = ["plants", "trees", "birds", "insects", "invalid"]
    overall_summary = {}

    for cat_dir in categories:
        target_path = os.path.join(DATA_DIR, cat_dir)
        if not os.path.exists(target_path):
            print(f"Skipping {cat_dir}: directory not found.")
            continue

        file_list = [f for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))]

        provider_category = "plant" if cat_dir in ("plants", "trees") else ("bird" if cat_dir == "birds" else ("insect" if cat_dir == "insects" else "unknown"))
        provider = get_identification_provider(provider_category)

        total_images = len(file_list)
        failed_requests = 0
        low_confidence_results = 0
        successful_predictions = 0
        total_time_sec = 0.0

        print(f"\n--- Testing Category: {cat_dir.upper()} ({total_images} images) ---")

        for fname in file_list:
            fpath = os.path.join(target_path, fname)
            ext = os.path.splitext(fname)[1].lower()
            mime_type = "text/plain" if ext == ".txt" else ("image/png" if ext == ".png" else "image/jpeg")

            try:
                with open(fpath, "rb") as f:
                    file_bytes = f.read()

                # Validate image
                try:
                    w, h, checksum = validate_image_file(file_bytes, fname, mime_type)
                except Exception as val_err:
                    detail_msg = getattr(val_err, 'detail', str(val_err))
                    print(f"  [REJECTED] [{fname}] Invalid image format: {detail_msg}")
                    failed_requests += 1
                    continue

                img_payload = [{
                    "file_bytes": file_bytes,
                    "filename": fname,
                    "organ": "auto"
                }]

                start_t = time.time()
                response = provider.identify(img_payload, category=provider_category)
                elapsed = time.time() - start_t
                total_time_sec += elapsed

                if not response.success:
                    err_msg = response.error.message if response.error else 'Unknown error'
                    print(f"  [FAILED] [{fname}] Request failed or unavailable: {err_msg}")
                    failed_requests += 1
                else:
                    successful_predictions += 1
                    top_pred = response.predictions[0] if response.predictions else None
                    top_sci = top_pred.scientific_name if top_pred else 'None'
                    top_conf = top_pred.confidence if top_pred else 0.0

                    if response.identification_status == "LOW_CONFIDENCE" or top_conf < 0.50:
                        low_confidence_results += 1
                        print(f"  [LOW CONF] [{fname}] Confidence: {top_conf*100:.1f}% -> Top: {top_sci} (Provider: {response.provider}) [{elapsed*1000:.0f}ms]")
                    else:
                        print(f"  [SUCCESS]  [{fname}] Confidence: {top_conf*100:.1f}% -> Top: {top_sci} (Provider: {response.provider}) [{elapsed*1000:.0f}ms]")

            except Exception as err:
                print(f"  [ERROR] [{fname}] Exception during test: {err}")
                failed_requests += 1

        avg_inference_ms = (total_time_sec / max(1, successful_predictions)) * 1000

        cat_stats = {
            "total_images": total_images,
            "successful_predictions": successful_predictions,
            "failed_requests": failed_requests,
            "low_confidence_results": low_confidence_results,
            "avg_inference_ms": round(avg_inference_ms, 2)
        }
        overall_summary[cat_dir] = cat_stats

        print(f"Summary for {cat_dir.upper()}: Total: {total_images} | Success: {successful_predictions} | Failed: {failed_requests} | Low Conf: {low_confidence_results} | Avg Time: {avg_inference_ms:.1f}ms")

    print("\n==========================================================")
    print("FINAL EVALUATION BENCHMARK SUMMARY")
    print("==========================================================")
    for cat, stats in overall_summary.items():
        print(f"* {cat.capitalize()}: {stats['total_images']} images | {stats['successful_predictions']} identified | {stats['failed_requests']} failed | {stats['low_confidence_results']} low-conf | {stats['avg_inference_ms']}ms avg")
    print("==========================================================")

if __name__ == "__main__":
    run_model_evaluation()
