import React, { useState, useEffect } from 'react';

<<<<<<< HEAD
// Use /api as base URL - nginx will proxy to backend
const API_BASE = '/api';
=======
const API_BASE = window.location.origin;
>>>>>>> b63ce5b308410698571f4a2fea1efe95c3f9c1dc

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [isSignUp, setIsSignUp] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [activeTab, setActiveTab] = useState('import');
  
  // App state
  const [user, setUser] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [groupName, setGroupName] = useState('Flatmates 2026');
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  
  const [groups, setGroups] = useState([]);
  const [activeGroupId, setActiveGroupId] = useState('');
  const [balances, setBalances] = useState(null);
  
  const [activeLedgerMember, setActiveLedgerMember] = useState('');
  const [ledgerItems, setLedgerItems] = useState([]);
  
  // Toast notifications
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Auth check on mount
  useEffect(() => {
    if (token) {
      fetchUser();
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/me/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.ok ? await res.json() : null;
        setUser(data);
      } else {
        logout();
      }
    } catch (err) {
      showToast('Backend server connection failed.', 'error');
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    const endpoint = isSignUp ? '/api/auth/register/' : '/api/auth/login/';
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        localStorage.setItem('token', data.token);
        setUser(data.user);
        showToast(isSignUp ? 'Registered successfully!' : 'Signed in successfully!', 'success');
      } else {
        showToast(data.error || 'Authentication failed.', 'error');
      }
    } catch (err) {
      showToast('Authentication connection error.', 'error');
    }
  };

  const logout = () => {
    setToken('');
    setUser(null);
    localStorage.removeItem('token');
    showToast('Signed out successfully.', 'info');
  };

  // Load Groups
  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/groups/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const groupList = Array.isArray(data) ? data : (data.results || []);
        setGroups(groupList);
        if (groupList.length > 0 && !activeGroupId) {
          setActiveGroupId(groupList[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (token) {
      fetchGroups();
    }
  }, [token, activeTab]);

  // Load Balances
  const fetchBalances = async () => {
    if (!activeGroupId) return;
    try {
      const res = await fetch(`${API_BASE}/api/groups/${activeGroupId}/balances/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBalances(data);
        if (data.users_summary.length > 0 && !activeLedgerMember) {
          setActiveLedgerMember(data.users_summary[0].username);
        }
      }
    } catch (err) {
      showToast('Failed to fetch group balances.', 'error');
    }
  };

  useEffect(() => {
    if (token && activeGroupId) {
      fetchBalances();
    }
  }, [token, activeGroupId]);

  // Load Ledger
  const fetchLedger = async () => {
    if (!activeGroupId || !activeLedgerMember) return;
    try {
      const res = await fetch(`${API_BASE}/api/groups/${activeGroupId}/breakdown/?username=${activeLedgerMember}`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setLedgerItems(data);
      }
    } catch (err) {
      showToast('Failed to load ledger history.', 'error');
    }
  };

  useEffect(() => {
    if (token && activeGroupId && activeLedgerMember) {
      fetchLedger();
    }
  }, [token, activeGroupId, activeLedgerMember]);

  // File Upload Handlers
  const handleDrag = (e) => {
    e.preventDefault();
    if (e.type === 'dragover') {
      setIsDragOver(true);
    } else {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    showToast('Analyzing and cleaning file...', 'info');
    try {
      const res = await fetch(`${API_BASE}/api/import/preview/`, {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setImportPreview(data);
        showToast('Ingestion preview loaded successfully.', 'success');
      } else {
        showToast(data.error || 'Failed to upload/parse file.', 'error');
      }
    } catch (err) {
      showToast('Connection to import engine failed.', 'error');
    }
  };

  const handleConfirmImport = async () => {
    if (!importPreview) return;
    setIsConfirmOpen(false);
    showToast('Confirming and building shared ledger database...', 'info');
    try {
      const res = await fetch(`${API_BASE}/api/import/confirm/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`
        },
        body: JSON.stringify({
          import_log_id: importPreview.import_log_id,
          group_name: groupName
        })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Import records confirmed and applied!', 'success');
        setActiveGroupId(data.group_id);
        setActiveTab('balances');
        setImportPreview(null);
      } else {
        showToast(data.error || 'Confirm ingestion failed.', 'error');
      }
    } catch (err) {
      showToast('Connection to ingestion engine failed.', 'error');
    }
  };

  return (
    <div className="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500 selection:text-white flex flex-col">
      {/* Background Gradients */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-500/5 blur-[120px]" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-900/80 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-indigo-400 rounded-xl shadow-lg shadow-indigo-500/20">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="font-display font-bold text-2xl tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              SettleFlow
            </span>
          </div>

          {user && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800/80 px-4 py-2 rounded-full text-sm">
                <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-slate-300 font-medium">{user.username}</span>
              </div>
              <button
                onClick={logout}
                className="bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white border border-rose-500/20 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 shadow-md shadow-rose-950/20"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-8 relative z-10">
        
        {/* Toast Alert */}
        {toast && (
          <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-2xl border shadow-2xl transition-all duration-500 transform translate-y-0
            ${toast.type === 'error' ? 'bg-rose-950/90 border-rose-800 text-rose-200' : 
              toast.type === 'info' ? 'bg-indigo-950/90 border-indigo-800 text-indigo-200' :
              'bg-emerald-950/90 border-emerald-800 text-emerald-200'}`}
          >
            <div className={`w-2.5 h-2.5 rounded-full ${toast.type === 'error' ? 'bg-rose-500' : toast.type === 'info' ? 'bg-indigo-400' : 'bg-emerald-500'}`} />
            <span className="text-sm font-semibold">{toast.message}</span>
          </div>
        )}

        {/* AUTHENTICATION */}
        {!token ? (
          <div className="flex justify-center items-center py-20">
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-8 max-w-md w-full shadow-2xl">
              <h2 className="text-3xl font-display font-bold text-center mb-1 bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                {isSignUp ? 'Create Admin' : 'Portal Sign In'}
              </h2>
              <p className="text-slate-400 text-sm text-center mb-6">
                {isSignUp ? 'Setup your shared expenses administrator account' : 'Access the SettleFlow engine ledger workspace'}
              </p>

              <form onSubmit={handleAuth} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Username</label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter username"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-600"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-300"
                >
                  {isSignUp ? 'Register Account' : 'Authenticate'}
                </button>
              </form>

              <div className="text-center mt-6 text-sm text-slate-400">
                {isSignUp ? 'Already registered?' : "Don't have an account?"}{' '}
                <button
                  onClick={() => setIsSignUp(!isSignUp)}
                  className="text-indigo-400 hover:text-indigo-300 font-semibold focus:outline-none transition-colors"
                >
                  {isSignUp ? 'Sign In' : 'Sign Up'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* WORKSPACE DASHBOARD */
          <div className="space-y-6">
            
            {/* Tabs */}
            <div className="flex gap-1.5 border-b border-slate-900 pb-2">
              {[
                { id: 'import', label: 'Import Engine' },
                { id: 'balances', label: 'Group Balances' },
                { id: 'ledger', label: 'Audit Ledger' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-300 border
                    ${activeTab === tab.id 
                      ? 'bg-indigo-600/10 border-indigo-500/30 text-indigo-400 shadow-md shadow-indigo-950/15' 
                      : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* TAB CONTENT: IMPORT */}
            {activeTab === 'import' && (
              <div className="space-y-6">
                
                {/* Drag and Drop */}
                <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-8 shadow-xl">
                  <div className="mb-4">
                    <h3 className="text-xl font-bold font-display bg-gradient-to-r from-white to-slate-200 bg-clip-text text-transparent">
                      Upload Expense Spreadsheet
                    </h3>
                    <p className="text-slate-400 text-sm">Ingest raw ledger files and automatically run normalization rules.</p>
                  </div>

                  <div
                    onDragOver={handleDrag}
                    onDragLeave={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('fileInput').click()}
                    className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center
                      ${isDragOver 
                        ? 'border-indigo-500 bg-indigo-500/5' 
                        : 'border-slate-800 hover:border-indigo-500/60 bg-slate-950/30 hover:bg-indigo-950/5'}`}
                  >
                    <svg className={`w-12 h-12 mb-4 transition-colors duration-300 ${isDragOver ? 'text-indigo-400' : 'text-slate-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-slate-300 text-sm font-medium">
                      Drag and drop your <span className="text-indigo-400 font-bold">CSV or Excel sheet</span> here
                    </p>
                    <p className="text-slate-500 text-xs mt-1">Accepts .xlsx, .csv files</p>
                    <input
                      type="file"
                      id="fileInput"
                      accept=".xlsx,.csv"
                      className="hidden"
                      onChange={handleFileChange}
                    />
                  </div>
                </div>

                {/* Import Preview */}
                {importPreview && (
                  <div className="space-y-6">
                    {/* Summary cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {[
                        { label: 'Rows Scanned', val: importPreview.summary.total_rows_scanned, color: 'text-white' },
                        { label: 'Anomalies Identified', val: importPreview.summary.total_anomalies_detected, color: 'text-amber-400' },
                        { label: 'Clean Expenses Logged', val: importPreview.summary.valid_expenses_count, color: 'text-emerald-400' }
                      ].map((card, idx) => (
                        <div key={idx} className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 flex flex-col items-center justify-center">
                          <span className={`text-4xl font-display font-extrabold ${card.color} mb-1`}>{card.val}</span>
                          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">{card.label}</span>
                        </div>
                      ))}
                    </div>

                    {/* Anomalies Log */}
                    <div className="bg-slate-900/60 border border-slate-800/80 rounded-3xl p-6 shadow-xl space-y-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-xl font-bold font-display text-white">Spreadsheet Anomalies Log</h3>
                          <p className="text-slate-400 text-xs">Verify corrections made by the parsing rule engine.</p>
                        </div>
                        <button
                          onClick={() => setIsConfirmOpen(true)}
                          className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-300 text-sm"
                        >
                          Confirm & Ingest In Database
                        </button>
                      </div>

                      <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950/40">
                        <table className="w-full text-left text-sm border-collapse">
                          <thead>
                            <tr className="bg-slate-900 border-b border-slate-800 text-slate-300 font-semibold">
                              <th className="p-4">Row</th>
                              <th className="p-4">Column</th>
                              <th className="p-4">Anomaly Type</th>
                              <th className="p-4">Severity</th>
                              <th className="p-4">Description</th>
                              <th className="p-4">Resolution Policy Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800">
                            {importPreview.anomalies.length === 0 ? (
                              <tr>
                                <td colSpan="6" className="p-8 text-center text-slate-500">
                                  No anomalies found! The spreadsheet was successfully validated with clean records.
                                </td>
                              </tr>
                            ) : (
                              importPreview.anomalies.map((anom, idx) => (
                                <tr
                                  key={idx}
                                  className={`hover:bg-slate-900/20 transition-all
                                    ${anom.severity === 'high' ? 'border-l-2 border-l-rose-500' : anom.severity === 'medium' ? 'border-l-2 border-l-amber-500' : 'border-l-2 border-l-emerald-500'}`}
                                >
                                  <td className="p-4 font-mono text-slate-300">{anom.row || 'N/A'}</td>
                                  <td className="p-4 font-mono text-indigo-400"><code>{anom.field}</code></td>
                                  <td className="p-4 text-slate-200">{anom.type}</td>
                                  <td className="p-4">
                                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase border
                                      ${anom.severity === 'high' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' : 
                                        anom.severity === 'medium' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 
                                        'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'}`}
                                    >
                                      {anom.severity}
                                    </span>
                                  </td>
                                  <td className="p-4 text-slate-300 max-w-xs md:max-w-sm truncate" title={anom.description}>
                                    {anom.description}
                                  </td>
                                  <td className="p-4 text-slate-400 max-w-xs md:max-w-sm truncate" title={anom.policy_action}>
                                    {anom.policy_action}
                                  </td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB CONTENT: BALANCES */}
            {activeTab === 'balances' && (
              <div className="space-y-6">
                
                {/* Selector */}
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-3xl p-6 shadow-xl flex flex-wrap justify-between items-center gap-4">
                  <div>
                    <h3 className="text-xl font-bold font-display text-white">Net Group Balances</h3>
                    <p className="text-slate-400 text-xs">Verify who owes whom and net balances after resolving anomalies.</p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <label className="text-sm font-semibold text-slate-300">Active Group:</label>
                    <select
                      value={activeGroupId}
                      onChange={(e) => setActiveGroupId(e.target.value)}
                      className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500 transition-all cursor-pointer"
                    >
                      <option value="">Select Group</option>
                      {groups.map(g => (
                        <option key={g.id} value={g.id}>{g.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {balances ? (
                  <div className="space-y-6">
                    
                    {/* Grid of net balances */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {balances.users_summary.map((member, idx) => {
                        const net = parseFloat(member.net_balance);
                        const isPositive = net >= 0;
                        return (
                          <div key={idx} className="bg-slate-900/40 border border-slate-800/85 hover:border-slate-700/85 rounded-2xl p-6 shadow-md transition-all duration-300">
                            <div className="flex justify-between items-center border-b border-slate-800 pb-3 mb-4">
                              <span className="font-display font-bold text-lg text-white">{member.username}</span>
                              <span className={`font-display font-extrabold text-lg ${isPositive ? 'text-emerald-400' : 'text-rose-500'}`}>
                                {isPositive ? '+' : ''}{net.toFixed(2)} INR
                              </span>
                            </div>
                            <div className="space-y-2 text-sm text-slate-400">
                              <div className="flex justify-between">
                                <span>Total Contributed:</span>
                                <span className="text-slate-200 font-semibold">{parseFloat(member.paid_amount).toFixed(2)} INR</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Split Share Cost:</span>
                                <span className="text-slate-200 font-semibold">{parseFloat(member.share_amount).toFixed(2)} INR</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Settlements Sent:</span>
                                <span className="text-slate-200 font-semibold">{parseFloat(member.settlements_sent).toFixed(2)} INR</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Settlements Recd:</span>
                                <span className="text-slate-200 font-semibold">{parseFloat(member.settlements_received).toFixed(2)} INR</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Simplified Debts */}
                    <div className="bg-gradient-to-br from-indigo-950/20 to-emerald-950/5 border border-indigo-900/30 rounded-3xl p-6 shadow-xl">
                      <h4 className="font-display font-bold text-lg text-white mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Optimized Debt Settlement Path
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {balances.simplified_debts.length === 0 ? (
                          <div className="col-span-2 text-center py-6 text-slate-500 text-sm">
                            Group is fully balanced. No settlements required!
                          </div>
                        ) : (
                          balances.simplified_debts.map((debt, idx) => (
                            <div key={idx} className="bg-slate-950/60 border border-slate-900 p-4 rounded-xl flex justify-between items-center">
                              <div className="flex items-center gap-2.5 text-sm">
                                <span className="font-bold text-slate-200">{debt.from_user}</span>
                                <span className="text-indigo-400 font-bold">➔</span>
                                <span className="font-bold text-slate-300">{debt.to_user}</span>
                              </div>
                              <span className="font-display font-extrabold text-emerald-400">{parseFloat(debt.amount).toFixed(2)} INR</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-900/30 border border-slate-900 rounded-3xl py-20 text-center text-slate-500">
                    No active group data. Upload a sheet and confirm ingestion to calculate balances.
                  </div>
                )}
              </div>
            )}

            {/* TAB CONTENT: LEDGER */}
            {activeTab === 'ledger' && (
              <div className="space-y-6">
                
                {/* Header selectors */}
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-3xl p-6 shadow-xl flex flex-wrap justify-between items-center gap-4">
                  <div>
                    <h3 className="text-xl font-bold font-display text-white">Chronological Audit Trail</h3>
                    <p className="text-slate-400 text-xs">Drill down into a specific user's transactions and running ledger balance.</p>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2">
                      <label className="text-sm font-semibold text-slate-300">Group:</label>
                      <select
                        value={activeGroupId}
                        onChange={(e) => setActiveGroupId(e.target.value)}
                        className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500 transition-all cursor-pointer"
                      >
                        <option value="">Select Group</option>
                        {groups.map(g => (
                          <option key={g.id} value={g.id}>{g.name}</option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <label className="text-sm font-semibold text-slate-300">Member:</label>
                      <select
                        value={activeLedgerMember}
                        onChange={(e) => setActiveLedgerMember(e.target.value)}
                        className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-indigo-500 transition-all cursor-pointer"
                      >
                        <option value="">Select Member</option>
                        {balances && balances.users_summary.map(u => (
                          <option key={u.username} value={u.username}>{u.username}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {ledgerItems.length > 0 ? (
                  <div className="bg-slate-900/60 border border-slate-800/80 rounded-3xl p-6 shadow-xl">
                    <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950/40">
                      <table className="w-full text-left text-sm border-collapse">
                        <thead>
                          <tr className="bg-slate-900 border-b border-slate-800 text-slate-300 font-semibold">
                            <th className="p-4">Date</th>
                            <th className="p-4">Description</th>
                            <th className="p-4">Total Paid (User)</th>
                            <th className="p-4">Split Share</th>
                            <th className="p-4">Net Contribution Impact</th>
                            <th className="p-4">Running Balance</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {ledgerItems.map((item, idx) => {
                            const net = parseFloat(item.net_effect);
                            const isPositive = net >= 0;
                            return (
                              <tr key={idx} className="hover:bg-slate-900/20 transition-all">
                                <td className="p-4 font-mono text-slate-400">{item.date}</td>
                                <td className="p-4">
                                  <div className="font-semibold text-slate-200">{item.description}</div>
                                  <div className="text-xs text-slate-500 mt-0.5">
                                    Payer: {item.paid_by} | Original: {parseFloat(item.original_amount).toFixed(2)} {item.currency}
                                  </div>
                                </td>
                                <td className="p-4 text-slate-300">{parseFloat(item.user_paid_in_base).toFixed(2)} INR</td>
                                <td className="p-4 text-slate-300">{parseFloat(item.user_share_in_base).toFixed(2)} INR</td>
                                <td className={`p-4 font-semibold ${isPositive ? 'text-emerald-400' : 'text-rose-500'}`}>
                                  {isPositive ? '+' : ''}{net.toFixed(2)} INR
                                </td>
                                <td className="p-4 font-bold text-slate-200">{parseFloat(item.running_balance).toFixed(2)} INR</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-900/30 border border-slate-900 rounded-3xl py-20 text-center text-slate-500">
                    No ledger history loaded. Select both a group and a flatmate to view chronological ledger actions.
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Confirmation Modal */}
      {isConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <div>
              <h3 className="text-xl font-bold font-display text-white mb-2">Confirm Ledger Ingestion</h3>
              <p className="text-slate-400 text-sm">
                This will save all normalized expenses, currency conversions, and Temporal Memberships under the designated group.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Group Name</label>
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="Enter group name"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setIsConfirmOpen(false)}
                className="bg-slate-950 border border-slate-800 hover:bg-slate-900 text-slate-300 font-semibold px-5 py-2.5 rounded-xl text-sm transition-all duration-300"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmImport}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-300"
              >
                Confirm & Create Group
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500 mt-8">
        SettleFlow Shared Expenses System &copy; {new Date().getFullYear()}. Built with React & Tailwind CSS.
      </footer>
    </div>
  );
}
