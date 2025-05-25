import { Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@/components/Icon';

export default function Header({to, name}: {to: string, name: string}) {
    return (
        <div className="flex items-center bg-white p-4 pb-3 justify-between sticky top-0 z-10 shadow-sm border-b border-gray-200">
            <div className="text-black flex size-12 shrink-0 items-center justify-center rounded-full hover:bg-gray-100 transition-colors">
                <Link to={to}>
                    <ArrowLeftIcon />
                </Link>
            </div>
            <h2 className="text-black text-xl font-bold tracking-tight flex-1 text-center pr-12">{name}</h2>
        </div>
    )
}