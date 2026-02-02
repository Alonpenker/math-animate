from pathlib import Path

class PathNames:
    ARTIFACTS_FOLDER = 'job_artifacts'
    MANIM_CODE = 'code.py'
    
    TMP_RENDER_FOLDER = '/tmp/render'
    INPUT_FOLDER = 'input'
    OUTPUT_FOLDER = 'output'
    
class DockerCommands:
    BIN = ("docker", "run", "--rm")
    NETWORK = ("--network","none")
    CPU = ("--cpus","1")
    MEMORY = ("--memory","2g")
    
    @staticmethod
    def volume(src: Path, dst: str, mode: str):
        return ("-v", f"{src}:{dst}:{mode}")
    
    IMAGE = ("manimcommunity/manim:latest",)
    SHELL = ("/bin/sh", "-c")
    
    @staticmethod
    def manim_command(code_name: str, scene_name: str):
        return (
            f"manim -qh /input/{code_name} {scene_name} > /dev/null 2>&1"
        )
        
