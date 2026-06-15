import icon from '@/assets/Logo.png';
import { Link } from 'react-router-dom';

const QuickOrderWelcome = () => {
    return (
        <div className="relative flex h-screen flex-col bg-[#FFFBF5] justify-between overflow-x-hidden">
            <div className="flex-1 flex flex-col justify-center items-center px-8">
                <div className="mb-8 text-center animate-fade-in">
                    <div className="mb-6">
                        <img src={icon} alt="Logo" className="w-28 h-28 mx-auto rounded-3xl shadow-xl border-2 border-[#EDE8E1]" />
                    </div>
                    <h1 className="text-[#2D2A26] text-3xl font-bold mb-2">晨間廚房</h1>
                    <p className="text-[#6B6660] text-base">選擇您偏好的點餐方式</p>
                </div>

                <div className="w-full max-w-sm space-y-4">
                    <Link
                        to="/voiceorder"
                        className="group flex items-center justify-center gap-3 w-full h-16 bg-gradient-to-r from-[#F5A623] to-[#FF7A00] text-white text-lg font-bold rounded-2xl hover:shadow-xl hover:shadow-[#F5A623]/20 active:scale-97 transition-all duration-200"
                    >
                        <span className="text-xl">🎙️</span>
                        <span>語音點餐</span>
                    </Link>

                    <Link
                        to="/menu"
                        className="group flex items-center justify-center gap-3 w-full h-16 bg-white border-2 border-[#EDE8E1] text-[#2D2A26] text-lg font-bold rounded-2xl hover:border-[#D4CEC7] hover:shadow-md active:scale-97 transition-all duration-200"
                    >
                        <span className="text-xl">📋</span>
                        <span>手動選單</span>
                    </Link>
                </div>

                <div className="mt-12 grid grid-cols-3 gap-3 w-full max-w-sm">
                    {[
                        { icon: '⚡', label: '快速' },
                        { icon: '🎯', label: '精準' },
                        { icon: '💬', label: '互動' },
                    ].map(({ icon: ic, label }) => (
                        <div key={label} className="text-center p-4 bg-white rounded-2xl border border-[#EDE8E1] shadow-sm">
                            <div className="text-2xl mb-1">{ic}</div>
                            <p className="text-[#6B6660] text-xs font-medium">{label}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="p-6 text-center">
                <p className="text-[#9C9690] text-sm">輕觸按鈕開始您的點餐體驗</p>
            </div>
        </div>
    );
};

export default QuickOrderWelcome;