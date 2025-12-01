"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Mail, Phone } from "lucide-react";

export default function ContactsPage() {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        const res = await api.get("/contacts");
        setContacts(res.data);
      } catch (error) {
        console.error("Failed to fetch contacts", error);
      } finally {
        setLoading(false);
      }
    };
    fetchContacts();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Contacts</h2>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {contacts.map((contact) => (
          <div 
            key={contact.id} 
            className="rounded-xl border bg-white p-6 shadow-sm transition-all hover:shadow-md dark:bg-gray-800 dark:border-gray-700"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{contact.name || contact.email}</h3>
              <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium dark:bg-gray-700">
                {contact.pipeline_stage}
              </span>
            </div>
            
            <div className="mt-4 space-y-2 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                {contact.email}
              </div>
              {contact.phone && (
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  {contact.phone}
                </div>
              )}
            </div>
            
            {contact.profile_summary && (
              <div className="mt-4 border-t pt-4">
                <p className="text-xs text-gray-500 line-clamp-3">
                  {contact.profile_summary}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
