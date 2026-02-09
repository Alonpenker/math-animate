from pathlib import Path

class PathNames:
    ARTIFACTS_FOLDER = 'job_artifacts'
    MANIM_CODE = 'code.py'
    
    TMP_RENDER_FOLDER = '/job'
    INPUT_FOLDER = 'input'
    OUTPUT_FOLDER = 'output'
    MEDIA_FOLDER = 'media'
    VIDEOS_FOLDER = 'videos'
    RESOLUTION_FOLDER = '1080p60'
    PARTIAL_MOVIE_FILES_FOLDER = 'partial_movie_files'
    
class DockerCommands:
    BIN = ("docker", "run", "--rm")
    NETWORK = ("--network","none")
    CPU = ("--cpus","1")
    MEMORY = ("--memory","2g")
    PIDS = ("--pids-limit", "256")
    SECURITY = (
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
    )
    
    @staticmethod
    def volume(src: str, dst: Path, mode: str):
        return ("-v", f"{src}:{dst}:{mode}")
    
    IMAGE = ("manimcommunity/manim",)
    
    @staticmethod
    def manim_command(code_path: Path, media_dir: Path):
        return (
            "manim",
            "-qh",
            "-a",
            "--media_dir",
            f"{media_dir}",
            f"{code_path}"
        )
        
