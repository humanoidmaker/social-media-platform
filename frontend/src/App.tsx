import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
interface AuthCtx { user: any; isAuth: boolean; loading: boolean; login: (e: string, p: string) => Promise<void>; logout: () => void; }
const AuthContext = createContext<AuthCtx>({} as AuthCtx);
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null); const [loading, setLoading] = useState(true);
  useEffect(() => { const t = localStorage.getItem('nh_token'); const u = localStorage.getItem('nh_uid'); if (t && u) setUser({ id: u }); setLoading(false); }, []);
  const login = async (e: string, p: string) => { const r = await axios.post(`${API}/api/auth/login`, { email: e, password: p }); localStorage.setItem('nh_token', r.data.access_token); localStorage.setItem('nh_uid', r.data.user_id); setUser({ id: r.data.user_id }); };
  const logout = () => { localStorage.removeItem('nh_token'); localStorage.removeItem('nh_uid'); setUser(null); };
  return <AuthContext.Provider value={{ user, isAuth: !!user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
const useAuth = () => useContext(AuthContext);

const client = axios.create({ baseURL: API });
client.interceptors.request.use(c => { const t = localStorage.getItem('nh_token'); if (t) c.headers.Authorization = `Bearer ${t}`; return c; });

function Layout() {
  const { logout } = useAuth();
  const nav = [{ to: '/', label: 'Feed' }, { to: '/explore', label: 'Explore' }, { to: '/messages', label: 'Messages' }, { to: '/notifications', label: 'Notifications' }, { to: '/profile', label: 'Profile' }, { to: '/stories', label: 'Stories' }, { to: '/collections', label: 'Collections' }, { to: '/settings', label: 'Settings' }];
  return (<div className="flex h-screen bg-gray-50 dark:bg-gray-900"><aside className="w-56 bg-white dark:bg-gray-800 border-r p-4 hidden md:block"><h1 className="text-xl font-bold text-pink-600 mb-6">Social Media Platform</h1><nav className="space-y-1">{nav.map(n => <a key={n.to} href={n.to} className="block px-3 py-2 rounded text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">{n.label}</a>)}</nav><button onClick={logout} className="mt-8 text-sm text-gray-400 hover:text-red-400">Logout</button></aside><main className="flex-1 overflow-y-auto"><Routes><Route index element={<FeedPage />} /><Route path="explore" element={<DataPage title="Explore" endpoint="/api/search/trending" />} /><Route path="messages" element={<DataPage title="Messages" endpoint="/api/messages" />} /><Route path="notifications" element={<DataPage title="Notifications" endpoint="/api/notifications" />} /><Route path="profile" element={<DataPage title="Profile" endpoint="/api/users/me" />} /><Route path="stories" element={<DataPage title="Stories" endpoint="/api/stories" />} /><Route path="collections" element={<DataPage title="Collections" endpoint="/api/collections" />} /><Route path="settings" element={<div className="p-6"><h1 className="text-2xl font-bold dark:text-white">Settings</h1></div>} /><Route path="user/:username" element={<DataPage title="Profile" endpoint="/api/users/me" />} /><Route path="post/:id" element={<DataPage title="Post" endpoint="/api/posts" />} /></Routes></main></div>);
}

function FeedPage() {
  const [posts, setPosts] = useState<any[]>([]); const [loading, setLoading] = useState(true); const [newPost, setNewPost] = useState('');
  useEffect(() => { client.get('/api/feed').then(r => setPosts(Array.isArray(r.data) ? r.data : r.data.items || [])).catch(() => {}).finally(() => setLoading(false)); }, []);
  const createPost = async () => { if (!newPost.trim()) return; await client.post('/api/posts', { content_text: newPost, post_type: 'text' }); setNewPost(''); client.get('/api/feed').then(r => setPosts(Array.isArray(r.data) ? r.data : r.data.items || [])); };
  return (<div className="max-w-2xl mx-auto p-6 space-y-6"><h1 className="text-2xl font-bold dark:text-white">Feed</h1><div className="bg-white dark:bg-gray-800 rounded-lg p-4 border"><textarea value={newPost} onChange={e => setNewPost(e.target.value)} placeholder="What's on your mind?" rows={3} className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white resize-none" /><button onClick={createPost} className="mt-2 px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700">Post</button></div>{loading ? <div className="animate-pulse space-y-4">{[1,2,3].map(i => <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg" />)}</div> : posts.map((p: any, i) => <div key={p.id || i} className="bg-white dark:bg-gray-800 rounded-lg p-4 border"><p className="text-sm font-medium dark:text-gray-300 mb-1">@{p.author_username || 'user'}</p><p className="dark:text-gray-400">{p.content_text}</p><div className="flex gap-4 mt-3 text-sm text-gray-500"><span>{p.like_count || 0} likes</span><span>{p.comment_count || 0} comments</span><span>{p.repost_count || 0} reposts</span></div></div>)}</div>);
}

function DataPage({ title, endpoint }: { title: string; endpoint: string }) {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(true);
  useEffect(() => { client.get(endpoint).then(r => setData(r.data)).catch(() => {}).finally(() => setLoading(false)); }, [endpoint]);
  return (<div className="max-w-2xl mx-auto p-6"><h1 className="text-2xl font-bold mb-6 dark:text-white">{title}</h1>{loading ? <div className="animate-pulse h-32 bg-gray-200 dark:bg-gray-700 rounded-lg" /> : <pre className="bg-white dark:bg-gray-800 rounded-lg p-6 border text-sm overflow-auto max-h-96 dark:text-gray-300">{JSON.stringify(data, null, 2)}</pre>}</div>);
}

function Login() {
  const [email, setEmail] = useState(''); const [pw, setPw] = useState(''); const [err, setErr] = useState(''); const { login } = useAuth();
  return (<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-500 to-purple-600"><div className="bg-white rounded-xl p-8 w-96 shadow-xl"><h1 className="text-3xl font-bold text-center bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent mb-6">Social Media Platform</h1>{err && <p className="text-red-500 text-sm mb-4">{err}</p>}<form onSubmit={async e => { e.preventDefault(); try { await login(email, pw); window.location.href = '/'; } catch { setErr('Invalid credentials'); } }} className="space-y-4"><input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" className="w-full px-3 py-2 border rounded-lg" /><input type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder="Password" className="w-full px-3 py-2 border rounded-lg" /><button className="w-full bg-gradient-to-r from-pink-600 to-purple-600 text-white py-2 rounded-lg">Sign In</button></form></div></div>);
}

export default function App() {
  return (<AuthProvider><Routes><Route path="/login" element={<Login />} /><Route path="/*" element={(() => { const { isAuth, loading } = useAuth(); if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>; return isAuth ? <Layout /> : <Navigate to="/login" />; })()} /></Routes></AuthProvider>);
}
