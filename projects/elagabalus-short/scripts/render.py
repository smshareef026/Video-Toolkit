import sys, json
sys.path.insert(0, '.')
from tools.video.video_compose import VideoCompose
scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
out = sys.argv[2] if len(sys.argv) > 2 else 'projects/elagabalus-short/renders/elagabalus_short_final.mp4'
bespoke = {"entry": "projects/elagabalus-short/composition/index.tsx", "composition_id": "ElagabalusShort",
           "public_dir": "projects/elagabalus-short/public", "crf": 18}
if scale != 1.0:
    bespoke["scale"] = scale
r = VideoCompose().execute({"operation": "render", "output_path": out,
    "edit_decisions": {"composition_mode": "atelier", "render_runtime": "remotion", "bespoke": bespoke}})
print(r.success, r.error, json.dumps(r.data, default=str)[:600])
