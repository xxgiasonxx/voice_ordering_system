import React from 'react';

// --- Button ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  className = '',
  children,
  disabled,
  ...props
}) => {
  const base = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100';

  const variants = {
    primary: 'bg-[#F5A623] text-white hover:bg-[#E8951A] shadow-sm hover:shadow-md',
    secondary: 'bg-[#50B4EA] text-white hover:bg-[#4AA3D9] shadow-sm hover:shadow-md',
    ghost: 'bg-transparent text-[#2D2A26] hover:bg-[#EDE8E1]',
    danger: 'bg-[#FF3B30] text-white hover:bg-[#E5332B] shadow-sm',
  };

  const sizes = {
    sm: 'h-9 px-4 text-sm gap-1.5',
    md: 'h-11 px-5 text-base gap-2',
    lg: 'h-14 px-6 text-lg gap-2.5',
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : null}
      {children}
    </button>
  );
};

// --- Card ---
interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick, hoverable = false }) => (
  <div
    className={`bg-white rounded-2xl border border-[#EDE8E1] shadow-card ${hoverable ? 'hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer' : ''} ${className}`}
    onClick={onClick}
  >
    {children}
  </div>
);

// --- Badge ---
interface BadgeProps {
  children: React.ReactNode;
  color?: 'orange' | 'blue' | 'green' | 'gray';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ children, color = 'orange', size = 'sm' }) => {
  const colors = {
    orange: 'bg-[#FFF3E0] text-[#E8951A] border border-[#FFE0B2]',
    blue: 'bg-[#E3F2FD] text-[#1976D2] border border-[#BBDEFB]',
    green: 'bg-[#E8F5E9] text-[#388E3C] border border-[#C8E6C9]',
    gray: 'bg-[#F5F5F5] text-[#6B6660] border border-[#E0E0E0]',
  };
  const sizes = { sm: 'text-xs px-2 py-0.5', md: 'text-sm px-3 py-1' };
  return (
    <span className={`inline-flex items-center rounded-full font-medium ${colors[color]} ${sizes[size]}`}>
      {children}
    </span>
  );
};

// --- Quantity Selector ---
interface QuantitySelectorProps {
  value: number;
  onChange: (val: number) => void;
  min?: number;
  max?: number;
  size?: 'sm' | 'md';
}

export const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  value, onChange, min = 0, max = 99, size = 'md'
}) => {
  const btnSize = size === 'sm' ? 'w-7 h-7' : 'w-9 h-9';
  const textSize = size === 'sm' ? 'w-7 text-sm' : 'w-10 text-base';
  return (
    <div className="inline-flex items-center gap-1 bg-[#F5F3EF] rounded-xl overflow-hidden border border-[#EDE8E1]">
      <button
        className={`${btnSize} flex items-center justify-center text-[#6B6660] hover:bg-[#EDE8E1] transition-colors disabled:opacity-40`}
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 7h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
      <span className={`${textSize} text-center font-semibold text-[#2D2A26] tabular-nums`}>{value}</span>
      <button
        className={`${btnSize} flex items-center justify-center text-[#6B6660] hover:bg-[#EDE8E1] transition-colors disabled:opacity-40`}
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 3v8M3 7h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
};

// --- Bottom Tab Bar ---
interface TabItem {
  id: string;
  label: string;
  icon: React.FC<{ className?: string }>;
  active?: boolean;
  onClick: () => void;
  href?: string;
}

interface BottomTabBarProps {
  tabs: TabItem[];
}

export const BottomTabBar: React.FC<BottomTabBarProps> = ({ tabs }) => (
  <div className="flex border-t border-[#EDE8E1] bg-white px-2 pb-2 pt-1.5 safe-bottom">
    {tabs.map((tab) => {
      const Icon = tab.icon;
      const active = tab.active;
      return (
        <button
          key={tab.id}
          onClick={tab.onClick}
          className={`flex flex-1 flex-col items-center justify-end gap-0.5 py-1.5 transition-colors ${active ? 'text-[#F5A623]' : 'text-[#9C9690]'}`}
        >
          <div className={active ? 'text-[#F5A623]' : 'text-[#9C9690]'}>
            <Icon className="w-6 h-6" />
          </div>
          <span className={`text-xs font-medium ${active ? 'text-[#F5A623]' : 'text-[#9C9690]'}`}>
            {tab.label}
          </span>
        </button>
      );
    })}
  </div>
);

// --- Divider ---
export const Divider: React.FC<{ label?: string }> = ({ label }) => (
  <div className="flex items-center gap-3">
    <div className="flex-1 h-px bg-[#EDE8E1]" />
    {label && <span className="text-xs text-[#9C9690] font-medium">{label}</span>}
    {label && <div className="flex-1 h-px bg-[#EDE8E1]" />}
  </div>
);

// --- Empty State ---
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
    {icon && <div className="mb-4 text-[#D4CEC7]">{icon}</div>}
    <p className="text-[#2D2A26] font-semibold text-base mb-1">{title}</p>
    {description && <p className="text-[#9C9690] text-sm mb-4 max-w-xs">{description}</p>}
    {action}
  </div>
);

// --- Loading Skeleton ---
export const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-[#EDE8E1] rounded-xl ${className}`} />
);