"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { API_BASE_URL } from "../../lib/config";
import { Users, UserPlus, Edit, Lock, CheckCircle, XCircle, Trash2 } from "lucide-react";

interface User {
  user_id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  display_name?: string;
  created_at: string;
  last_login?: string;
}

export default function UserManagement() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const isAdmin = user?.role === "ADMIN";
  const isManager = user?.role === "MANAGER" || isAdmin;

  // Filter users based on search term
  const filteredUsers = users.filter(u => 
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.display_name && u.display_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  useEffect(() => {
    if (isManager) {
      fetchUsers();
    }
  }, [isManager]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/auth/users`, {
        headers: {
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        }
      });

      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (formData: {
    username: string;
    email: string;
    role: string;
    display_name?: string;
    password?: string;
  }) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        const data = await res.json();
        alert(`✅ User created!\n\n${data.temporary_password ? `Temporary password: ${data.temporary_password}\n\nNote: Share this password securely. The user should change it on first login.` : 'User created successfully'}`);
        fetchUsers();
        setShowCreateModal(false);
      } else {
        const error = await res.json();
        alert(`❌ Error: ${error.detail || 'Failed to create user'}`);
      }
    } catch (error) {
      alert(`❌ Error creating user: ${error}`);
    }
  };

  const handleUpdateUser = async (userId: string, updates: {
    role?: string;
    is_active?: boolean;
    display_name?: string;
  }) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/users/${userId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        },
        body: JSON.stringify(updates)
      });

      if (res.ok) {
        alert("✅ User updated successfully");
        fetchUsers();
        setEditingUser(null);
      } else {
        const error = await res.json();
        alert(`❌ Error: ${error.detail || 'Failed to update user'}`);
      }
    } catch (error) {
      alert(`❌ Error updating user: ${error}`);
    }
  };

  const handleResetPassword = async (userId: string, username: string) => {
    const newPassword = prompt(`Enter new password for ${username}:`);
    if (!newPassword) return;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/users/${userId}/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        },
        body: JSON.stringify({ new_password: newPassword })
      });

      if (res.ok) {
        alert(`✅ Password reset successfully for ${username}`);
      } else {
        const error = await res.json();
        alert(`❌ Error: ${error.detail || 'Failed to reset password'}`);
      }
    } catch (error) {
      alert(`❌ Error resetting password: ${error}`);
    }
  };

  if (!isManager) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--text-secondary)]">
          You don't have permission to manage users.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--text-secondary)]">Loading users...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Users className="w-5 h-5" />
            User Management
          </h3>
          <p className="text-sm text-[var(--text-secondary)]">
            Manage users in your organization
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2 transition-colors"
        >
          <UserPlus className="w-4 h-4" />
          Create User
        </button>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="Search by username or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Users Table */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-[var(--surface-hover)] border-b border-[var(--border)]">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">User</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Email</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Role</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Last Login</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            {filteredUsers.map((u) => (
              <tr key={u.user_id} className="hover:bg-[var(--surface-hover)] transition-colors">
                <td className="px-4 py-3">
                  <div>
                    <div className="font-medium">{u.username}</div>
                    {u.display_name && u.display_name !== u.username && (
                      <div className="text-xs text-[var(--text-secondary)]">{u.display_name}</div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">{u.email}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    u.role === 'ADMIN' ? 'bg-red-500/20 text-red-300' :
                    u.role === 'MANAGER' ? 'bg-blue-500/20 text-blue-300' :
                    u.role === 'COLLABORATOR' ? 'bg-green-500/20 text-green-300' :
                    'bg-gray-500/20 text-gray-300'
                  }`}>
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {u.is_active ? (
                    <span className="flex items-center gap-1 text-green-400 text-sm">
                      <CheckCircle className="w-4 h-4" /> Active
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-red-400 text-sm">
                      <XCircle className="w-4 h-4" /> Inactive
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                  {u.last_login ? new Date(u.last_login).toLocaleDateString('es-ES', { 
                    year: 'numeric', month: 'short', day: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                  }) : 'Never'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setEditingUser(u)}
                      className="p-1.5 hover:bg-[var(--text-primary)]/10 rounded transition-colors"
                      title="Edit user"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleResetPassword(u.user_id, u.username)}
                      className="p-1.5 hover:bg-[var(--text-primary)]/10 rounded transition-colors"
                      title="Reset password"
                    >
                      <Lock className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <div className="text-center py-12 text-[var(--text-secondary)]">
            No users found. Create your first user to get started.
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateUser}
          isAdmin={isAdmin}
        />
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onUpdate={handleUpdateUser}
          isAdmin={isAdmin}
        />
      )}
    </div>
  );
}

// Create User Modal Component
function CreateUserModal({ onClose, onCreate, isAdmin }: {
  onClose: () => void;
  onCreate: (data: any) => void;
  isAdmin: boolean;
}) {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    role: "COLLABORATOR",
    display_name: "",
    password: ""
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Create New User</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username *</label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email *</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Role *</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {isAdmin && <option value="MANAGER">MANAGER</option>}
              <option value="COLLABORATOR">COLLABORATOR</option>
              <option value="VIEWER">VIEWER</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Display Name</label>
            <input
              type="text"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password (optional)</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Auto-generated if empty"
            />
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Leave empty to auto-generate a secure password
            </p>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-[var(--border)] rounded hover:bg-[var(--surface-hover)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
            >
              Create User
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Edit User Modal Component
function EditUserModal({ user, onClose, onUpdate, isAdmin }: {
  user: User;
  onClose: () => void;
  onUpdate: (userId: string, updates: any) => void;
  isAdmin: boolean;
}) {
  const [formData, setFormData] = useState({
    role: user.role,
    is_active: user.is_active,
    display_name: user.display_name || "",
    email: user.email
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdate(user.user_id, formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Edit User: {user.username}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={user.role === "MANAGER" && !isAdmin}
            >
              {(isAdmin || user.role === "MANAGER") && <option value="MANAGER">MANAGER</option>}
              <option value="COLLABORATOR">COLLABORATOR</option>
              <option value="VIEWER">VIEWER</option>
            </select>
            {user.role === "MANAGER" && !isAdmin && (
              <p className="text-xs text-yellow-500 mt-1">
                ⚠️ Only ADMIN can change MANAGER roles
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Display Name</label>
            <input
              type="text"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded border-[var(--border)]"
            />
            <label htmlFor="is_active" className="text-sm font-medium">Active</label>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-[var(--border)] rounded hover:bg-[var(--surface-hover)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
