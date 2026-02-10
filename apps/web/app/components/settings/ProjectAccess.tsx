"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { Users, UserPlus, UserMinus, Edit, FolderOpen } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8085";

interface Project {
  project_id: string;
  name: string;
}

interface ProjectMember {
  user_id: string;
  username: string;
  email: string;
  display_name?: string;
  role: string;
  added_at: string;
}

interface User {
  user_id: string;
  username: string;
  email: string;
  role: string;
  display_name?: string;
}

export default function ProjectAccess() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedRole, setSelectedRole] = useState("COLLABORATOR");

  const isManager = user?.role === "MANAGER" || user?.role === "ADMIN";

  useEffect(() => {
    if (isManager) {
      fetchProjects();
      fetchAvailableUsers();
    }
  }, [isManager]);

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/projects`, {
        headers: {
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        }
      });

      if (res.ok) {
        const data = await res.json();
        // The endpoint returns an array directly, not {projects: [...]}
        const projectsList = Array.isArray(data) ? data : [];
        console.log("Projects loaded:", projectsList);
        setProjects(projectsList);
      } else {
        console.error("Failed to fetch projects:", res.status, await res.text());
      }
    } catch (error) {
      console.error("Error fetching projects:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableUsers = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/users`, {
        headers: {
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        }
      });

      if (res.ok) {
        const data = await res.json();
        // Filter only COLLABORATOR and VIEWER users
        const eligibleUsers = data.users.filter(
          (u: User) => u.role === "COLLABORATOR" || u.role === "VIEWER"
        );
        setAvailableUsers(eligibleUsers);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const fetchProjectMembers = async (projectId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/projects/${projectId}/members`, {
        headers: {
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        }
      });

      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
      }
    } catch (error) {
      console.error("Error fetching project members:", error);
    }
  };

  const handleSelectProject = (project: Project) => {
    setSelectedProject(project);
    fetchProjectMembers(project.project_id);
  };

  const handleAddMember = async () => {
    if (!selectedProject || !selectedUserId) return;

    try {
      const res = await fetch(`${API_BASE_URL}/projects/${selectedProject.project_id}/members`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        },
        body: JSON.stringify({
          user_id: selectedUserId,
          role: selectedRole
        })
      });

      if (res.ok) {
        alert(`✅ User added to project as ${selectedRole}`);
        fetchProjectMembers(selectedProject.project_id);
        setShowAddModal(false);
        setSelectedUserId("");
        setSelectedRole("COLLABORATOR");
      } else {
        const error = await res.json();
        alert(`❌ Error: ${error.detail || 'Failed to add user'}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error}`);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!selectedProject) return;
    
    if (!confirm("Remove this user from the project?")) return;

    try {
      const res = await fetch(`${API_BASE_URL}/projects/${selectedProject.project_id}/members/${userId}`, {
        method: "DELETE",
        headers: {
          "x-tenant-id": user?.tenant_id || "",
          "x-user-id": user?.user_id || "",
          "x-role": user?.role || ""
        }
      });

      if (res.ok) {
        alert("✅ User removed from project");
        fetchProjectMembers(selectedProject.project_id);
      } else {
        const error = await res.json();
        alert(`❌ Error: ${error.detail || 'Failed to remove user'}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error}`);
    }
  };

  if (!isManager) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--text-secondary)]">
          You don't have permission to manage project access.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--text-secondary)]">Loading projects...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FolderOpen className="w-5 h-5" />
          Project Access Management
        </h3>
        <p className="text-sm text-[var(--text-secondary)]">
          Assign COLLABORATOR and VIEWER users to specific projects. MANAGER users have automatic access to all projects.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects List */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4">
          <h4 className="font-medium mb-3 flex items-center gap-2">
            <FolderOpen className="w-4 h-4" />
            Projects ({projects.length})
          </h4>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {projects.length === 0 ? (
              <p className="text-[var(--text-secondary)] text-sm">No projects found</p>
            ) : (
              projects.map((proj) => (
                <button
                  key={proj.project_id}
                  onClick={() => handleSelectProject(proj)}
                  className={`w-full text-left px-3 py-2 rounded border transition-colors ${
                    selectedProject?.project_id === proj.project_id
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-[var(--border)] hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  <div className="font-medium text-sm">{proj.name}</div>
                  <div className="text-xs text-[var(--text-secondary)] truncate">{proj.project_id}</div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Project Members */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4">
          {selectedProject ? (
            <>
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-medium flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Members of "{selectedProject.name}"
                </h4>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm flex items-center gap-1.5"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  Add
                </button>
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {members.length === 0 ? (
                  <p className="text-[var(--text-secondary)] text-sm">No members assigned yet</p>
                ) : (
                  members.map((member) => (
                    <div
                      key={member.user_id}
                      className="flex items-center justify-between px-3 py-2 border border-[var(--border)] rounded"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{member.username}</div>
                        <div className="text-xs text-[var(--text-secondary)]">{member.email}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            member.role === "COLLABORATOR"
                              ? "bg-green-500/20 text-green-300"
                              : "bg-gray-500/20 text-gray-300"
                          }`}
                        >
                          {member.role}
                        </span>
                        <button
                          onClick={() => handleRemoveMember(member.user_id)}
                          className="p-1 hover:bg-red-500/10 text-red-400 rounded"
                          title="Remove from project"
                        >
                          <UserMinus className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-[var(--text-secondary)]">
              <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Select a project to manage members</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAddModal(false)}>
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Add User to Project</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">User</label>
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a user...</option>
                  {availableUsers
                    .filter(u => !members.some(m => m.user_id === u.user_id))
                    .map(u => (
                      <option key={u.user_id} value={u.user_id}>
                        {u.username} ({u.email}) - {u.role}
                      </option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Role in Project</label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="COLLABORATOR">COLLABORATOR (can edit)</option>
                  <option value="VIEWER">VIEWER (read-only)</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-[var(--border)] rounded hover:bg-[var(--surface-hover)]"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddMember}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
                  disabled={!selectedUserId}
                >
                  Add to Project
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
