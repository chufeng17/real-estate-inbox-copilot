"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);
  const [resetting, setResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await api.get("/auth/me");
        setUser(res.data);
      } catch (error) {
        console.error("Failed to fetch user", error);
      }
    };
    fetchUser();
  }, []);

  const handleResetClick = () => {
    setShowConfirmDialog(true);
  };

  const handleConfirmReset = async () => {
    setShowConfirmDialog(false);
    console.log("Starting reset...");
    setResetting(true);
    setResetMessage(null);

    try {
      console.log("Calling API...");
      const res = await api.post("/admin/reset-demo");
      console.log("✅ Reset successful! Response:", res.data);
      
      const successMsg = {
        type: 'success' as const,
        text: `Deleted: ${res.data.deleted.contacts} contacts, ${res.data.deleted.email_threads} threads, ${res.data.deleted.email_messages} messages, ${res.data.deleted.tasks} tasks, ${res.data.deleted.embeddings} embeddings.`
      };
      
      console.log("Setting success message:", successMsg);
      setResetMessage(successMsg);
    } catch (error: any) {
      console.error("❌ Reset failed:", error);
      const errorMessage = error.response?.data?.detail || error.message || "Failed to reset demo";
      
      const errorMsg = {
        type: 'error' as const,
        text: errorMessage
      };
      
      console.log("Setting error message:", errorMsg);
      setResetMessage(errorMsg);
    } finally {
      console.log("Resetting complete, setting resetting=false");
      setResetting(false);
    }
  };

  const handleCancelReset = () => {
    setShowConfirmDialog(false);
  };

  if (!user) return <div>Loading...</div>;

  return (
    <>
      {/* Confirmation Modal */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full p-6 border-2 border-red-500">
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Confirm Reset
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                This will <strong className="text-red-600 dark:text-red-400">permanently DELETE</strong> all:
              </p>
              <ul className="text-left text-gray-700 dark:text-gray-300 space-y-2 mb-4">
                <li>• All contacts</li>
                <li>• All email threads and messages</li>
                <li>• All tasks</li>
                <li>• All embeddings</li>
              </ul>
              <p className="text-sm text-green-700 dark:text-green-400 font-medium">
                ✓ User accounts will be preserved
              </p>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={handleCancelReset}
                className="flex-1 px-4 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReset}
                className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                Yes, Reset Demo
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-2xl space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        
        <div className="rounded-xl border bg-white p-6 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <h3 className="text-lg font-medium mb-4">Profile Information</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Name</label>
              <div className="mt-1 p-2 bg-gray-50 rounded border dark:bg-gray-700 dark:border-gray-600">
                {user.name || "Not set"}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Email</label>
              <div className="mt-1 p-2 bg-gray-50 rounded border dark:bg-gray-700 dark:border-gray-600">
                {user.email}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Role</label>
              <div className="mt-1 p-2 bg-gray-50 rounded border dark:bg-gray-700 dark:border-gray-600 capitalize">
                {user.role}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-6 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <h3 className="text-lg font-medium mb-4">Demo Management</h3>
          
          {resetMessage && (
            <div className={`mb-4 p-4 rounded-lg border-2 ${
              resetMessage.type === 'success' 
                ? 'bg-green-50 text-green-900 border-green-300 dark:bg-green-900/30 dark:text-green-200 dark:border-green-700' 
                : 'bg-red-50 text-red-900 border-red-300 dark:bg-red-900/30 dark:text-red-200 dark:border-red-700'
            }`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <p className="font-medium mb-1">
                    {resetMessage.type === 'success' ? '✅ Reset Successful!' : '❌ Reset Failed'}
                  </p>
                  <p className="text-sm">{resetMessage.text}</p>
                </div>
                <button
                  onClick={() => setResetMessage(null)}
                  className="flex-shrink-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Reset the demo to a clean state while preserving user accounts.
              This will delete all contacts, email threads, messages, tasks, and embeddings.
            </p>
            <p className="text-sm text-yellow-700 dark:text-yellow-500 font-medium">
              ⚠️ Admin access required. For testing/demo purposes only.
            </p>
            <button
              type="button"
              onClick={handleResetClick}
              disabled={resetting}
              className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                resetting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400'
                  : 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800'
              }`}
            >
              {resetting ? 'Resetting Demo...' : '🗑️ Reset Demo Data'}
            </button>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-6 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <h3 className="text-lg font-medium mb-4">Application Settings</h3>
          <p className="text-sm text-gray-500">
            Configuration is managed via environment variables in this demo.
          </p>
        </div>
      </div>
    </>
  );
}
