import React from 'react';

export function CategoryBadge({ category }) {
  const cat = (category || 'unknown').toLowerCase();
  return <span className={`badge badge-${cat}`}>{cat.toUpperCase()}</span>;
}

export function VerificationBadge({ status }) {
  const st = (status || 'pending').toLowerCase();
  let label = st.replace('_', ' ');
  if (st === 'user_confirmed') label = 'User Confirmed';
  if (st === 'ai_suggested') label = 'AI Suggested';
  if (st === 'user_corrected') label = 'User Corrected';
  
  return <span className={`badge badge-${st}`}>{label}</span>;
}

export function MockBadge() {
  return <span className="badge badge-mock">DEMO / MOCK RESULT</span>;
}
