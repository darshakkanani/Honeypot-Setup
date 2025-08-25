import React from 'react';
import './StatCard.css';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: string;
  trend?: number;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, trend }) => {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-title">{title}</div>
        {trend !== undefined && (
          <div className={`stat-trend ${trend >= 0 ? 'positive' : 'negative'}`}>
            {trend >= 0 ? '↗' : '↘'} {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
