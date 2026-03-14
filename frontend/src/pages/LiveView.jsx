import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, CheckCircle, AlertCircle, Loader } from 'lucide-react';

export default function LiveView() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [job, setJob] = useState(null);
    const [logs, setLogs] = useState('');
    const [imgStamp, setImgStamp] = useState(Date.now());
    const logEndRef = useRef(null);

    useEffect(() => {
        let interval;

        const fetchStatus = async () => {
            try {
                const [jobRes, logsRes] = await Promise.all([
                    api.get(`/job/${id}`),
                    api.get(`/job/${id}/logs`)
                ]);

                setJob(jobRes.data);
                setLogs(logsRes.data.logs);
                setImgStamp(Date.now());

                if (jobRes.data.status === 'completed' || jobRes.data.status === 'failed') {
                    clearInterval(interval);
                }
            } catch (err) {
                console.error(err);
            }
        };

        fetchStatus();
        interval = setInterval(fetchStatus, 1500); // Poll every 1.5s

        return () => clearInterval(interval);
    }, [id]);

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    if (!job) return <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}><div className="spinner" style={{ borderColor: 'var(--primary)', borderLeftColor: 'transparent' }}></div></div>;

    return (
        <div className="app-container">
            <nav className="navbar">
                <button className="btn btn-secondary" onClick={() => navigate('/dashboard')} style={{ padding: '0.5rem', border: 'none', background: 'transparent' }}>
                    <ArrowLeft size={20} color="var(--text-main)" />
                </button>
                <div className="nav-brand" style={{ fontSize: '1rem' }}>
                    Live Sync Process #{id}
                </div>
                <div style={{ width: 32 }}></div>
            </nav>

            <main className="container" style={{ maxWidth: '900px' }}>
                <div className="card mb-6" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem' }}>
                    <div>
                        <h3 style={{ marginBottom: '0.25rem' }}>Sync Execution Viewer</h3>
                        <p style={{ fontSize: '0.875rem' }}>Date Filter: {job.start_date_filter} | Started: {new Date(job.created_at).toLocaleString()}</p>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.875rem' }}>
                        {job.status === 'running' && <><Loader size={18} className="spinner" /> RUNNING</>}
                        {job.status === 'completed' && <><CheckCircle size={18} color="var(--success)" /> COMPLETED</>}
                        {job.status === 'failed' && <><AlertCircle size={18} color="var(--error)" /> FAILED</>}
                        {job.status === 'pending' && <><Loader size={18} className="spinner" /> PENDING</>}
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                    {job.status !== 'pending' && (
                        <div style={{ background: '#000', borderRadius: '0.5rem', overflow: 'hidden', border: '1px solid var(--border-color)', position: 'relative', minHeight: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <img
                                src={`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/job/${id}/stream?t=${imgStamp}`}
                                alt="Live Web Stream"
                                style={{ width: '100%', height: 'auto', display: 'block' }}
                                onError={(e) => {
                                    e.target.style.display = 'none'; e.target.parentElement.innerHTML = '<div style="color:var(--text-muted);padding:2rem;">Waiting for browser stream to initialize...</div>';
                                }}
                                onLoad={(e) => { e.target.style.display = 'block'; }}
                            />
                        </div>
                    )}

                    <div className="log-terminal" style={{ margin: 0, height: '400px' }}>
                        {logs ? (
                            logs.split('\n').map((line, i) => (
                                <div key={i} className="log-line">{line}</div>
                            ))
                        ) : (
                            <div style={{ color: 'var(--text-muted)' }}>Waiting for process to output logs...</div>
                        )}
                        <div ref={logEndRef} />
                    </div>
                </div>

                {job.status === 'completed' && (
                    <div className="mt-6 text-center" style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', borderRadius: '0.5rem', border: '1px solid var(--success)' }}>
                        Process finished successfully. The internship diary is synchronized!
                    </div>
                )}
            </main>
        </div>
    );
}
