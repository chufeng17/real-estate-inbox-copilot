"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format } from "date-fns";
import { CheckCircle, Clock, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const TodayPage = () => {
  const [agenda, setAgenda] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAgenda = async () => {
    try {
      const res = await api.get("/agenda/today");
      setAgenda(res.data);
    } catch (error) {
      console.error("Failed to fetch agenda", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgenda();
  }, []);

  const markComplete = async (taskId: number) => {
    try {
      await api.patch(`/tasks/${taskId}`, { status: "DONE" });
      fetchAgenda(); // Refresh
    } catch (error) {
      console.error("Failed to update task", error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Today's Agenda</h2>
      
      <div className="space-y-4">
        {agenda.length === 0 && (
          <div className="text-gray-500">No tasks for today!</div>
        )}
        
        {agenda.map((task) => {
          const isOverdue = task.overdue;
          
          return (
            <div 
              key={task.id} 
              className={cn(
                "flex items-center justify-between rounded-lg border p-4 shadow-sm transition-all hover:shadow-md",
                isOverdue ? "border-red-200 bg-red-50 dark:bg-red-900/10" : "bg-white dark:bg-gray-800"
              )}
            >
              <div className="flex items-start gap-4">
                <button 
                  onClick={() => markComplete(task.id)}
                  className="mt-1 text-gray-400 hover:text-green-600"
                >
                  <CheckCircle className="h-6 w-6" />
                </button>
                <div>
                  <h3 className="font-medium">{task.title}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {task.task_type} • Priority: {task.priority}
                  </p>
                  {task.due_date && (
                    <div className={cn("mt-1 flex items-center text-xs", isOverdue ? "text-red-600" : "text-gray-500")}>
                      <Clock className="mr-1 h-3 w-3" />
                      {format(new Date(task.due_date), "MMM d, h:mm a")}
                      {isOverdue && <span className="ml-2 font-bold">(Overdue)</span>}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="text-right">
                <span className={cn(
                  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                  task.status === "OPEN" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"
                )}>
                  {task.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TodayPage;
