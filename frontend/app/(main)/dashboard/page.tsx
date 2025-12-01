"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // Assuming we might make these later, but for now I'll inline styles or make simple components
import { Users, CheckSquare, AlertCircle } from "lucide-react";
import { toast } from "sonner";

// Simple Card components to avoid complex shadcn setup for now
function SimpleCard({ title, value, icon: Icon, color }: any) {
  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm dark:bg-gray-800 dark:border-gray-700">
      <div className="flex items-center justify-between space-y-0 pb-2">
        <h3 className="text-sm font-medium tracking-tight text-gray-500 dark:text-gray-400">{title}</h3>
        <Icon className={`h-4 w-4 ${color}`} />
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState({
    contacts: 0,
    tasksOpen: 0,
    tasksOverdue: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [contactsRes, tasksRes] = await Promise.all([
          api.get("/contacts"),
          api.get("/tasks?status=OPEN"),
        ]);
        
        const tasks = tasksRes.data;
        const overdue = tasks.filter((t: any) => t.overdue).length;

        setStats({
          contacts: contactsRes.data.length,
          tasksOpen: tasks.length,
          tasksOverdue: overdue,
        });
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSync = async () => {
    toast.promise(api.post("/sync/emails"), {
      loading: 'Syncing emails...',
      success: (data: any) => {
        return `Sync complete! Loaded ${data.data.count || 'some'} emails.`;
      },
      error: 'Sync failed',
      duration: 10000, // Keep it visible for 10 seconds
      closeButton: true, // Allow user to close it
    });
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <button 
          onClick={handleSync}
          className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          Sync Emails
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <SimpleCard 
          title="Total Contacts" 
          value={stats.contacts} 
          icon={Users} 
          color="text-blue-500" 
        />
        <SimpleCard 
          title="Open Tasks" 
          value={stats.tasksOpen} 
          icon={CheckSquare} 
          color="text-green-500" 
        />
        <SimpleCard 
          title="Overdue Tasks" 
          value={stats.tasksOverdue} 
          icon={AlertCircle} 
          color="text-red-500" 
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-4 rounded-xl border bg-white p-6 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <h3 className="mb-4 text-lg font-medium">Recent Activity</h3>
          <p className="text-sm text-gray-500">
            Activity feed coming soon...
          </p>
        </div>
      </div>
    </div>
  );
}
