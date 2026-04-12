"""
任务调度器模块
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Coroutine
import schedule
import time

from loguru import logger

class Scheduler:
    """任务调度器"""
    
    def __init__(self):
        self.jobs = {}
        self.schedule = schedule.Scheduler()
        self.is_running = False
        
    async def add_job(self, 
                     func: Callable[[], Coroutine], 
                     interval: Optional[int] = None,
                     minutes: Optional[int] = None,
                     hours: Optional[int] = None,
                     hour: Optional[int] = None,
                     minute: Optional[int] = None,
                     name: Optional[str] = None) -> str:
        """添加定时任务"""
        
        if not name:
            name = f"job_{len(self.jobs) + 1}"
            
        # 创建包装函数
        def job_wrapper():
            asyncio.create_task(self._run_job(func, name))
            
        # 根据参数设置调度
        job = None
        
        if interval:
            job = self.schedule.every(interval).seconds.do(job_wrapper)
        elif minutes:
            job = self.schedule.every(minutes).minutes.do(job_wrapper)
        elif hours:
            job = self.schedule.every(hours).hours.do(job_wrapper)
        elif hour is not None and minute is not None:
            job = self.schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(job_wrapper)
        elif hour is not None:
            job = self.schedule.every().hour.at(f":{hour:02d}").do(job_wrapper)
        elif minute is not None:
            job = self.schedule.every().minute.at(f":{minute:02d}").do(job_wrapper)
        else:
            # 默认每分钟执行
            job = self.schedule.every().minute.do(job_wrapper)
            
        if job:
            self.jobs[name] = {
                "job": job,
                "func": func,
                "last_run": None,
                "next_run": job.next_run,
                "run_count": 0,
                "error_count": 0
            }
            
            logger.info(f"添加任务: {name}, 下次执行: {job.next_run}")
            return name
            
        return None
        
    async def _run_job(self, func: Callable[[], Coroutine], name: str):
        """运行任务"""
        job_info = self.jobs.get(name)
        if not job_info:
            return
            
        start_time = time.time()
        logger.debug(f"开始执行任务: {name}")
        
        try:
            # 更新任务状态
            job_info["last_run"] = datetime.now()
            job_info["run_count"] += 1
            
            # 执行任务
            await func()
            
            # 记录执行时间
            elapsed = time.time() - start_time
            logger.debug(f"任务 {name} 执行完成，耗时: {elapsed:.2f}秒")
            
        except Exception as e:
            job_info["error_count"] += 1
            logger.error(f"任务 {name} 执行出错: {e}")
            
        finally:
            # 更新下次执行时间
            if job_info["job"] in self.schedule.jobs:
                job_info["next_run"] = job_info["job"].next_run
                
    async def remove_job(self, name: str) -> bool:
        """移除任务"""
        if name in self.jobs:
            job_info = self.jobs[name]
            self.schedule.cancel_job(job_info["job"])
            del self.jobs[name]
            logger.info(f"移除任务: {name}")
            return True
        return False
        
    async def get_job_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if name in self.jobs:
            job_info = self.jobs[name]
            return {
                "name": name,
                "last_run": job_info["last_run"],
                "next_run": job_info["next_run"],
                "run_count": job_info["run_count"],
                "error_count": job_info["error_count"],
                "success_rate": (job_info["run_count"] - job_info["error_count"]) / max(job_info["run_count"], 1)
            }
        return None
        
    async def get_all_jobs_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        status = {}
        for name in self.jobs:
            status[name] = await self.get_job_status(name)
        return status
        
    async def run_pending(self):
        """运行待执行的任务"""
        try:
            # 运行schedule的待执行任务
            self.schedule.run_pending()
            
            # 也可以在这里添加自定义的调度逻辑
            await self._check_stuck_jobs()
            
        except Exception as e:
            logger.error(f"运行调度任务时出错: {e}")
            
    async def _check_stuck_jobs(self):
        """检查卡住的任务"""
        current_time = datetime.now()
        
        for name, job_info in self.jobs.items():
            last_run = job_info["last_run"]
            
            if last_run:
                # 如果任务上次运行超过30分钟，且应该已经再次运行，但状态还是运行中
                # 这里可以添加重启逻辑
                time_since_last = (current_time - last_run).total_seconds() / 60
                
                if time_since_last > 30:
                    next_run = job_info.get("next_run")
                    if next_run and next_run < current_time:
                        logger.warning(f"任务 {name} 可能卡住，上次运行: {last_run}, 应该运行: {next_run}")
                        # 可以考虑重启任务或发送告警
                        
    async def clear_all_jobs(self):
        """清除所有任务"""
        for name in list(self.jobs.keys()):
            await self.remove_job(name)
        logger.info("已清除所有任务")
        
    def get_next_run_time(self) -> Optional[datetime]:
        """获取下一个任务的运行时间"""
        if self.schedule.jobs:
            return self.schedule.next_run
        return None
        
    async def run_once(self, name: str) -> bool:
        """立即运行一次任务"""
        if name in self.jobs:
            job_info = self.jobs[name]
            await self._run_job(job_info["func"], name)
            return True
        return False