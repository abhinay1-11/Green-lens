import React, { useEffect, useState } from 'react';
import { getTrendAnalytics } from '../services/api';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, BarChart2, PieChart as PieIcon } from 'lucide-react';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function Trends() {
  const [period, setPeriod] = useState('30d');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getTrendAnalytics(period)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [period]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Biodiversity Trends & Analytics</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Temporal species activity, category accumulation curves, and campus zone distribution
          </p>
        </div>

        {/* Time Period Filter */}
        <div className="glass-panel" style={{ padding: '6px', display: 'flex', gap: '4px' }}>
          {['7d', '30d', '90d', '365d'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className="btn"
              style={{
                padding: '6px 14px',
                fontSize: '0.8rem',
                background: period === p ? 'var(--accent-primary)' : 'transparent',
                color: period === p ? '#fff' : 'var(--text-muted)'
              }}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : p === '90d' ? '3 Months' : '1 Year'}
            </button>
          ))}
        </div>
      </div>

      {/* Time-Series Area Chart */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={20} color="var(--accent-primary)" /> Observations Over Time
        </h3>

        <div style={{ width: '100%', height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data?.trend_points || []}>
              <defs>
                <linearGradient id="colorPlant" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorBird" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorInsect" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="var(--text-dim)" fontSize={12} />
              <YAxis stroke="var(--text-dim)" fontSize={12} />
              <Tooltip contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-glass)', borderRadius: '8px', color: '#fff' }} />
              <Area type="monotone" dataKey="plants" stackId="1" stroke="#10b981" fillOpacity={1} fill="url(#colorPlant)" name="Plants" />
              <Area type="monotone" dataKey="birds" stackId="1" stroke="#3b82f6" fillOpacity={1} fill="url(#colorBird)" name="Birds" />
              <Area type="monotone" dataKey="insects" stackId="1" stroke="#f59e0b" fillOpacity={1} fill="url(#colorInsect)" name="Insects" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid: Top Species Bar Chart & Zone Pie Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Top Species Bar Chart */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart2 size={18} color="var(--accent-secondary)" /> Most Logged Species
          </h3>

          <div style={{ width: '100%', height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.top_species || []} layout="vertical">
                <XAxis type="number" stroke="var(--text-dim)" fontSize={11} />
                <YAxis dataKey="common_name" type="category" stroke="var(--text-dim)" fontSize={11} width={100} />
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-glass)', color: '#fff' }} />
                <Bar dataKey="count" fill="var(--accent-primary)" radius={[0, 4, 4, 0]} name="Recorded Logs" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Zone Activity Distribution */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PieIcon size={18} color="#8b5cf6" /> Campus Zone Activity
          </h3>

          <div style={{ width: '100%', height: '260px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.zone_activity || []}
                  dataKey="count"
                  nameKey="zone"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {(data?.zone_activity || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border-glass)', color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
