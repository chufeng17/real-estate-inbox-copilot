"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { format } from "date-fns";
import { Mail, ArrowRight, User } from "lucide-react";

export default function ThreadsPage() {
  const [threads, setThreads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedThread, setSelectedThread] = useState<any>(null);

  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const res = await api.get("/email-threads");
        setThreads(res.data);
      } catch (error) {
        console.error("Failed to fetch threads", error);
      } finally {
        setLoading(false);
      }
    };
    fetchThreads();
  }, []);

  const fetchThreadDetails = async (threadId: number) => {
    try {
      const res = await api.get(`/email-threads/${threadId}`);
      setSelectedThread(res.data);
    } catch (error) {
      console.error("Failed to fetch thread details", error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      {/* Thread List */}
      <div className="w-1/3 overflow-auto rounded-xl border bg-white shadow-sm dark:bg-gray-800 dark:border-gray-700">
        <div className="border-b p-4">
          <h2 className="text-xl font-bold">Inbox</h2>
        </div>
        <div className="divide-y">
          {threads.map((thread) => (
            <div 
              key={thread.id}
              onClick={() => fetchThreadDetails(thread.id)}
              className={`cursor-pointer p-4 hover:bg-gray-50 dark:hover:bg-gray-700 ${selectedThread?.id === thread.id ? "bg-blue-50 dark:bg-blue-900/20" : ""}`}
            >
              <div className="mb-1 flex justify-between">
                <span className="font-semibold truncate">{thread.subject}</span>
                <span className="text-xs text-gray-500">
                  {thread.last_message_at && format(new Date(thread.last_message_at), "MMM d")}
                </span>
              </div>
              <div className="text-sm text-gray-500 truncate">
                Thread ID: {thread.thread_id}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Thread Detail */}
      <div className="flex-1 overflow-auto rounded-xl border bg-white shadow-sm dark:bg-gray-800 dark:border-gray-700">
        {!selectedThread ? (
          <div className="flex h-full items-center justify-center text-gray-500">
            Select a thread to view messages
          </div>
        ) : (
          <div className="flex flex-col h-full">
            <div className="border-b p-6">
              <h2 className="text-2xl font-bold">{selectedThread.subject}</h2>
            </div>
            <div className="flex-1 overflow-auto p-6 space-y-6">
              {selectedThread.messages.map((msg: any) => (
                <div key={msg.id} className={`flex flex-col ${msg.direction === "OUTGOING" ? "items-end" : "items-start"}`}>
                  <div className={`max-w-[80%] rounded-lg p-4 ${msg.direction === "OUTGOING" ? "bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100" : "bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100"}`}>
                    <div className="mb-2 flex items-center justify-between gap-4 text-xs opacity-70">
                      <span className="font-semibold">{msg.from_email}</span>
                      <span>{format(new Date(msg.sent_at), "MMM d, h:mm a")}</span>
                    </div>
                    <div className="whitespace-pre-wrap text-sm">
                      {msg.body_text}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
