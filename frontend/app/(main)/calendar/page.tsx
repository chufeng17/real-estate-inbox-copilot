"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isToday } from "date-fns";

export default function CalendarPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const res = await api.get("/tasks");
        setTasks(res.data);
      } catch (error) {
        console.error("Failed to fetch tasks", error);
      }
    };
    fetchTasks();
  }, []);

  const days = eachDayOfInterval({
    start: startOfMonth(currentDate),
    end: endOfMonth(currentDate),
  });

  const getTasksForDay = (day: Date) => {
    return tasks.filter(task => 
      task.due_date && isSameDay(new Date(task.due_date), day)
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Calendar</h2>
        <div className="text-lg font-medium">
          {format(currentDate, "MMMM yyyy")}
        </div>
      </div>

      <div className="grid grid-cols-7 gap-4">
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
          <div key={day} className="text-center font-semibold text-gray-500">
            {day}
          </div>
        ))}
        
        {days.map((day) => {
          const dayTasks = getTasksForDay(day);
          return (
            <div 
              key={day.toString()} 
              className={`min-h-[120px] rounded-lg border p-2 ${isToday(day) ? "bg-blue-50 border-blue-200 dark:bg-blue-900/20" : "bg-white dark:bg-gray-800 dark:border-gray-700"}`}
            >
              <div className={`mb-2 text-right text-sm ${isToday(day) ? "font-bold text-blue-600" : "text-gray-500"}`}>
                {format(day, "d")}
              </div>
              <div className="space-y-1">
                {dayTasks.map((task) => (
                  <div 
                    key={task.id} 
                    className={`truncate rounded px-1 py-0.5 text-xs ${task.status === "DONE" ? "bg-green-100 text-green-800 line-through opacity-50" : "bg-blue-100 text-blue-800"}`}
                    title={task.title}
                  >
                    {task.title}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
