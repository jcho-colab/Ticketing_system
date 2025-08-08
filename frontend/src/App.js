import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Email Entry Component
const EmailForm = ({ onEmailSubmit }) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email) {
      setError('Email is required');
      return;
    }
    onEmailSubmit(email);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow-2xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Welcome to the Support Portal
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your email to create or view tickets.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Enter your email"
            />
          </div>
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Continue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ userEmail }) => {
  const [activeTab, setActiveTab] = useState('tickets');
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showTicketModal, setShowTicketModal] = useState(false);

  useEffect(() => {
    fetchTickets();
  }, [userEmail]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/tickets?email=${userEmail}`);
      setTickets(response.data);
    } catch (error) {
      console.error('Failed to fetch tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const openTicketModal = async (ticketId) => {
    try {
      const response = await axios.get(`${API}/tickets/${ticketId}`);
      setSelectedTicket(response.data);
      setShowTicketModal(true);
    } catch (error) {
      console.error('Failed to fetch ticket details:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Support Portal</h1>
              <p className="text-sm text-gray-600">Email: {userEmail}</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('tickets')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'tickets'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Tickets
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'create'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Create New Ticket
            </button>
            <button
              onClick={() => setActiveTab('kpi')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'kpi'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              KPI Dashboard
            </button>
          </nav>
        </div>

        {activeTab === 'tickets' && (
          <TicketsList tickets={tickets} loading={loading} onRefresh={fetchTickets} onTicketClick={openTicketModal} />
        )}
        {activeTab === 'create' && <CreateTicketForm onTicketCreated={fetchTickets} userEmail={userEmail} />}
        {activeTab === 'kpi' && <KpiDashboard />}
      </div>

      {showTicketModal && selectedTicket && (
        <TicketModal
          ticket={selectedTicket}
          onClose={() => setShowTicketModal(false)}
          onUpdate={fetchTickets}
          userEmail={userEmail}
        />
      )}
    </div>
  );
};

// Tickets List Component
const TicketsList = ({ tickets, loading, onRefresh, onTicketClick }) => {
    const getPriorityColor = (priority) => {
        switch (priority) {
          case 'critical': return 'bg-red-100 text-red-800';
          case 'high': return 'bg-orange-100 text-orange-800';
          case 'medium': return 'bg-yellow-100 text-yellow-800';
          case 'low': return 'bg-green-100 text-green-800';
          default: return 'bg-gray-100 text-gray-800';
        }
      };
    
      const getStatusColor = (status) => {
        switch (status) {
          case 'new': return 'bg-blue-100 text-blue-800';
          case 'blocked': return 'bg-red-100 text-red-800';
          case 'pending': return 'bg-yellow-100 text-yellow-800';
          case 'cancelled': return 'bg-gray-100 text-gray-800';
          case 'closed': return 'bg-green-100 text-green-800';
          default: return 'bg-gray-100 text-gray-800';
        }
      };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-medium text-gray-900">My Tickets</h2>
        <button
          onClick={onRefresh}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {tickets.length === 0 ? (
            <li className="px-6 py-12 text-center">
              <p className="text-gray-500">No tickets found. Create your first ticket!</p>
            </li>
          ) : (
            tickets.map((ticket) => (
              <li key={ticket.id} className="px-6 py-4 hover:bg-gray-50 cursor-pointer" onClick={() => onTicketClick(ticket.id)}>
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {ticket.title}
                      </h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(ticket.priority)}`}>
                        {ticket.priority}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(ticket.status)}`}>
                        {ticket.status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                      <span>#{ticket.id.substring(0, 8)}</span>
                      <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    <span className="capitalize">{ticket.category}</span>
                  </div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
};

// Create Ticket Form Component
const CreateTicketForm = ({ onTicketCreated, userEmail }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    category: 'general',
    department: 'GTS',
    email: userEmail,
  });
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleFormSubmit = async (event) => {
    event.preventDefault();

    if (!formData.title || !formData.description) {
      setError('Title and description are required');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      // Create FormData object for multipart/form-data
      const formDataObj = new FormData();
      formDataObj.append('title', formData.title);
      formDataObj.append('description', formData.description);
      formDataObj.append('priority', formData.priority);
      formDataObj.append('category', formData.category);
      formDataObj.append('department', formData.department);
      formDataObj.append('email', formData.email);
      
      // Add attachments if any
      if (attachments.length > 0) {
        attachments.forEach((file) => {
          formDataObj.append('attachments', file);
        });
      }

      console.log('Submitting ticket with data:', formData);
      console.log('API Endpoint:', `${API}/tickets`);
      
      const response = await axios.post(`${API}/tickets`, formDataObj, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status === 200) {
        setSuccess(true);
        setFormData({
          title: '',
          description: '',
          priority: 'medium',
          category: 'general',
          department: 'GTS',
          email: userEmail,
        });
        setAttachments([]);
        if (onTicketCreated) {
          onTicketCreated();
        }
        setTimeout(() => setSuccess(false), 5000);
      }
    } catch (error) {
      console.error('Error creating ticket:', error);
      if (error.response) {
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
        console.error('Error response headers:', error.response.headers);
      } else if (error.request) {
        console.error('Error request:', error.request);
      } else {
        console.error('Error message:', error.message);
      }
      setError(error.response?.data?.detail || 'Failed to create ticket. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAttachmentChange = (e) => {
    const files = Array.from(e.target.files);
    setAttachments(files);
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Create New Ticket</h2>
      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleFormSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-3 rounded">
              ✅ Ticket created successfully! You can view it in the "My Tickets" tab.
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700">Title</label>
            <input
              type="text"
              name="title"
              required
              maxLength={120}
              value={formData.title}
              onChange={handleInputChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Brief description of the issue"
            />
            <p className="mt-1 text-xs text-gray-500">{formData.title.length}/120 characters</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              name="description"
              required
              rows={4}
              value={formData.description}
              onChange={handleInputChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Detailed description of the issue..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Attachments</label>
            <input
              type="file"
              multiple
              onChange={handleAttachmentChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
            {attachments.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-gray-600">Selected files:</p>
                <ul className="list-disc pl-5 mt-1">
                  {attachments.map((file, index) => (
                    <li key={index} className="text-sm text-gray-600">{file.name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Priority</label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Category</label>
              <select
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="general">General</option>
                <option value="technical">Technical</option>
                <option value="billing">Billing</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Department</label>
              <select
                name="department"
                value={formData.department}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="GTS">GTS</option>
                <option value="Strategy">Strategy</option>
                <option value="Customs">Customs</option>
                <option value="Classification">Classification</option>
              </select>
            </div>
          </div>
          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Creating Ticket...' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Ticket Modal Component
const TicketModal = ({ ticket, onClose, onUpdate, userEmail }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [editablePriority, setEditablePriority] = useState(ticket.priority);
  const [editableCategory, setEditableCategory] = useState(ticket.category);
  const [editableStatus, setEditableStatus] = useState(ticket.status);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState('');
  const fileInputRef = React.useRef(null);

  useEffect(() => {
    fetchComments();
  }, [ticket.id]);

  const fetchComments = async () => {
    try {
      const response = await axios.get(`${API}/tickets/${ticket.id}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    }
  };

  const addComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API}/tickets/${ticket.id}/comments`, {
        content: newComment,
        email: userEmail,
      });
      setComments([...comments, response.data]);
      setNewComment('');
    } catch (error) {
      console.error('Failed to add comment:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTicket = async () => {
    setUpdating(true);
    setUpdateError('');
    try {
      await axios.put(`${API}/tickets/${ticket.id}`, {
        priority: editablePriority,
        category: editableCategory,
        status: editableStatus,
      });
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Failed to update ticket:', error);
      setUpdateError('Failed to update ticket. Please try again.');
    } finally {
      setUpdating(false);
    }
  };

  const handleDeleteAttachment = async (filename) => {
    if (window.confirm('Are you sure you want to delete this attachment?')) {
      try {
        await axios.delete(`${API}/tickets/${ticket.id}/attachments/${filename}`);
        onUpdate();
        onClose();
      } catch (error) {
        console.error('Failed to delete attachment:', error);
        alert('Failed to delete attachment.');
      }
    }
  };

  const handleAddNewAttachments = async (event) => {
    const files = event.target.files;
    if (files.length === 0) return;

    const formData = new FormData();
    for (const file of files) {
      formData.append('attachments', file);
    }

    try {
      await axios.post(`${API}/tickets/${ticket.id}/attachments`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Failed to add attachments:', error);
      alert('Failed to add attachments.');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-800';
      case 'blocked': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      case 'closed': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const renderAttachmentPreview = (attachment) => {
    const attachmentUrl = `${BACKEND_URL}/${attachment.filepath}`;
    const uniqueFilename = attachment.filepath.split('/').pop();
    const isImage = /\.(jpe?g|png|gif)$/i.test(attachment.filename);

    return (
        <div className="relative group">
            {isImage ? (
                <a href={attachmentUrl} target="_blank" rel="noopener noreferrer">
                    <img src={attachmentUrl} alt={attachment.filename} className="w-20 h-20 object-cover rounded-md" />
                </a>
            ) : (
                <a href={attachmentUrl} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                    {attachment.filename}
                </a>
            )}
            <button
                onClick={() => handleDeleteAttachment(uniqueFilename)}
                className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
            >
                &times;
            </button>
        </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-medium text-gray-900">{ticket.title}</h3>
              <select
                value={editablePriority}
                onChange={(e) => setEditablePriority(e.target.value)}
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(editablePriority)}`}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
              <select
                value={editableStatus}
                onChange={(e) => setEditableStatus(e.target.value)}
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(editableStatus)}`}
              >
                <option value="new">New</option>
                <option value="blocked">Blocked</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <div className="text-sm text-gray-500 space-x-4">
              <span>#{ticket.id.substring(0, 8)}</span>
              <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
          >
            ×
          </button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h4 className="font-medium text-gray-900 mb-2">Description</h4>
              <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
            </div>
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-4">Comments ({comments.length})</h4>
              <div className="space-y-4 max-h-64 overflow-y-auto">
                {comments.map((comment) => (
                  <div key={comment.id} className="p-3 rounded-lg bg-white border border-gray-200">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-sm">{comment.user_name}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{comment.content}</p>
                  </div>
                ))}
              </div>
            </div>
            <form onSubmit={addComment} className="space-y-4">
              <div>
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  rows={3}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading || !newComment.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add Comment'}
                </button>
              </div>
            </form>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-4">Ticket Details</h4>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700">Category</label>
                <select
                  value={editableCategory}
                  onChange={(e) => setEditableCategory(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm capitalize"
                >
                  <option value="general">General</option>
                  <option value="technical">Technical</option>
                  <option value="billing">Billing</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Department</label>
                <p className="text-sm text-gray-900 capitalize">{ticket.department}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Created</label>
                <p className="text-sm text-gray-900">{new Date(ticket.created_at).toLocaleString()}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Last Updated</label>
                <p className="text-sm text-gray-900">{new Date(ticket.updated_at).toLocaleString()}</p>
              </div>
              {ticket.attachments && ticket.attachments.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Attachments</label>
                  <div className="mt-2 grid grid-cols-2 gap-4">
                    {ticket.attachments.map((attachment, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        {renderAttachmentPreview(attachment)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
                 <div>
                    <input
                        type="file"
                        multiple
                        ref={fileInputRef}
                        onChange={handleAddNewAttachments}
                        className="hidden"
                    />
                    <button
                        onClick={() => fileInputRef.current.click()}
                        className="w-full mt-2 bg-gray-200 text-gray-800 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-300"
                    >
                        Add Attachment
                    </button>
                 </div>
            </div>
          </div>
        </div>
        <div className="mt-6 flex justify-end space-x-4">
            {updateError && (
                <p className="text-sm text-red-600 self-center">{updateError}</p>
            )}
            <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
            >
                Cancel
            </button>
            <button
                onClick={handleUpdateTicket}
                disabled={updating}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
                {updating ? 'Updating...' : 'Update Ticket'}
            </button>
        </div>
      </div>
    </div>
  );
};

// KPI Dashboard Component
const KpiDashboard = () => {
  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchKpiData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API}/dashboard/kpi`);
        setKpiData(response.data);
      } catch (err) {
        setError('Failed to fetch KPI data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchKpiData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500 text-center py-12">{error}</div>;
  }

  if (!kpiData) {
    return <div className="text-center py-12">No KPI data available.</div>;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">KPI Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Tickets per Week</h3>
          <ul>
            {Object.entries(kpiData.tickets_per_week).map(([week, count]) => (
              <li key={week} className="flex justify-between py-1">
                <span>Week {week}:</span>
                <span className="font-semibold">{count} tickets</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Tickets per Month</h3>
          <ul>
            {Object.entries(kpiData.tickets_per_month).map(([month, count]) => (
              <li key={month} className="flex justify-between py-1">
                <span>Month {month}:</span>
                <span className="font-semibold">{count} tickets</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white shadow rounded-lg p-6 md:col-span-2">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Average Resolution Time by Department (Hours)</h3>
          <ul>
            {Object.entries(kpiData.avg_resolution_time_by_department).map(([dept, time]) => (
              <li key={dept} className="flex justify-between py-1">
                <span>{dept}:</span>
                <span className="font-semibold">{Number(time).toFixed(2)} hours</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail'));

  const handleEmailSubmit = (email) => {
    localStorage.setItem('userEmail', email);
    setUserEmail(email);
  };

  if (!userEmail) {
    return <EmailForm onEmailSubmit={handleEmailSubmit} />;
  }

  return <Dashboard userEmail={userEmail} />;
}

export default App;