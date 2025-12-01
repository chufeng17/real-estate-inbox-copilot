"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format } from "date-fns";
import { CheckCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("OPEN");

  const fetchTasks = async () => {
    try {
      const res = await api.get(`/tasks?status=${filter}`);
      setTasks(res.data);
    } catch (error) {
      console.error("Failed to fetch tasks", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [filter]);

  const markComplete = async (taskId: number) => {
    try {
      await api.patch(`/tasks/${taskId}`, { status: "DONE" });
      fetchTasks();
    } catch (error) {
      console.error("Failed to update task", error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">All Tasks</h2>
        <select 
          value={filter} 
          onChange={(e) => setFilter(e.target.value)}
          className="rounded-md border p-2 text-sm dark:bg-gray-800"
        >
          <option value="OPEN">Open</option>
          <option value="DONE">Completed</option>
          <option value="WAITING_ON_CLIENT">Waiting</option>
        </select>
      </div>
      
      <div className="space-y-4">
        {tasks.length === 0 && (
          <div className="text-gray-500">No tasks found.</div>
        )}
        
        {tasks.map((task) => (
          <div 
            key={task.id} 
            className="flex items-center justify-between rounded-lg border bg-white p-4 shadow-sm dark:bg-gray-800 dark:border-gray-700"
          >
            <div className="flex items-start gap-4">
              {task.status !== "DONE" && (
                <button 
                  onClick={() => markComplete(task.id)}
                  className="mt-1 text-gray-400 hover:text-green-600"
                >
                  <CheckCircle className="h-6 w-6" />
                </button>
              )}
              <div>
                <h3 className={cn("font-medium", task.status === "DONE" && "line-through text-gray-500")}>
                  {task.title}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {task.task_type} • Priority: {task.priority}
                </p>
                {task.due_date && (
                  <div className="mt-1 flex items-center text-xs text-gray-500">
                    <Clock className="mr-1 h-3 w-3" />
                    {format(new Date(task.due_date), "MMM d, h:mm a")}
                  </div>
                )}
              </div>
            </div>
            
            <div className="text-right">
              <span className={cn(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                task.status === "OPEN" ? "bg-blue-100 text-blue-800" : 
                task.status === "DONE" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
              )}>
                {task.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
