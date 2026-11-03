from dataclasses import dataclass
import shutil, subprocess, psutil
@dataclass
class HardwareSnapshot:
    cpu:float; ram_percent:float; ram_used_gb:float; ram_total_gb:float; disk_percent:float; battery:float|None; gpu_name:str="Unavailable"; vram_used_gb:float|None=None; vram_total_gb:float|None=None; gpu_percent:float|None=None; temperature:float|None=None; cuda:bool=False
class HardwareMonitor:
    def _nvidia(self):
        if not shutil.which("nvidia-smi"): return "Unavailable",None,None,None,None,False
        try:
            a=subprocess.check_output(["nvidia-smi","--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu","--format=csv,noheader,nounits"],text=True,timeout=2).splitlines()[0].split(", ")
            return a[0],float(a[1])/1024,float(a[2])/1024,float(a[3]),float(a[4]),True
        except Exception: return "NVIDIA GPU (query unavailable)",None,None,None,None,False
    def snapshot(self):
        m=psutil.virtual_memory(); b=psutil.sensors_battery(); g,vu,vt,gp,t,c=self._nvidia()
        return HardwareSnapshot(psutil.cpu_percent(),m.percent,m.used/2**30,m.total/2**30,psutil.disk_usage(".").percent,b.percent if b else None,g,vu,vt,gp,t,c)
