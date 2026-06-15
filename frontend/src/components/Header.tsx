import { Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@/components/Icon';

interface HeaderProps {
  to?: string;
  name?: string;
  goto?: string;
  gotoName?: string;
  title?: string;
  leftIcon?: React.ReactNode;
  onLeftClick?: () => void;
}

export default function Header({ to, name, goto, gotoName, title, leftIcon, onLeftClick }: HeaderProps) {
  return (
    <div className="flex items-center bg-white p-4 pb-3 justify-between sticky top-0 z-10 shadow-sm border-b border-[var(--color-border)]">
      <div className="text-black flex size-12 shrink-0 items-center justify-center rounded-full hover:bg-gray-100 transition-colors">
        {leftIcon && onLeftClick ? (
          <button onClick={onLeftClick} className="p-2.5 rounded-full hover:bg-gray-100 transition-colors">
            {leftIcon}
          </button>
        ) : (
          <Link to={to || '/'}>
            <ArrowLeftIcon />
          </Link>
        )}
      </div>
      <h2 className="text-black text-xl font-bold tracking-tight flex-1 text-center pr-12">
        {title || name}
      </h2>
      {goto && gotoName && (
        <button className="flex items-center justify-center gap-2 w-16 h-10 bg-gradient-to-r from-[#50b4ea] to-[#77caf2] text-white text-lg font-semibold rounded-2xl hover:from-[#4aa3d9] hover:to-[#6bb9e1] active:scale-95 transition-all duration-200 shadow-lg hover:shadow-xl">
          <Link to={goto} className="text-sm font-medium">
            {gotoName}
          </Link>
        </button>
      )}
    </div>
  );
}