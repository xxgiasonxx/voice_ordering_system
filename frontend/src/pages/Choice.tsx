import icon from '@/assets/Logo.png';
import { Link } from 'react-router-dom';
import Header from '@/components/Header';
import { MicIcon, MenuIcon } from '@/components/Icon';

const QuickOrderWelcome = () => {
    return (
        <div
            className="relative flex h-screen flex-col bg-white justify-between overflow-x-hidden"
            style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
        >
            <Header to="/" name="點餐系統" />

            {/* Main Content */}
            <div className="flex-1 flex flex-col justify-center items-center px-6">
                {/* Welcome Section */}
                <div className="text-center mb-12">
                    <div className="mb-6">
                        <img src={icon} alt="Logo" className="w-24 h-24 mx-auto rounded-2xl shadow-lg  border-gray-300" />
                    </div>
                    <h1 className="text-black text-3xl font-bold mb-3">歡迎使用點餐系統</h1>
                    <p className="text-black text-lg">選擇您偏好的點餐方式</p>
                </div>

                {/* Choice Buttons */}
                <div className="w-full max-w-sm space-y-4">
                    <Link
                        to="/voiceorder"
                        className="group flex items-center justify-center gap-2 w-full h-16 bg-gradient-to-r from-[#50b4ea] to-[#77caf2] text-white text-lg font-semibold rounded-2xl hover:from-[#4aa3d9] hover:to-[#6bb9e1] active:scale-95 transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                        <MicIcon />
                        <span>語音點餐</span>

                    </Link>
                    
                    <Link
                        to="/menuorder"
                        className="group flex items-center justify-center gap-2 w-full h-16 bg-gradient-to-r from-[#fbb059] to-[#f5a843] text-white text-lg font-semibold rounded-2xl hover:from-[#f0a548] hover:to-[#ea9d38] active:scale-95 transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                        <MenuIcon />
                        <span>手動選單</span>
                    </Link>
                </div>

                {/* Features */}
                <div className="mt-12 grid grid-cols-2 gap-4 w-full max-w-sm">
                    <div className="text-center p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
                        <div className="text-2xl mb-2">⚡</div>
                        <p className="text-sm text-black font-medium">快速便捷</p>
                    </div>
                    <div className="text-center p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
                        <div className="text-2xl mb-2">🎯</div>
                        <p className="text-sm text-black font-medium">精準識別</p>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-6 text-center">
                <p className="text-black text-sm">輕觸按鈕開始您的點餐體驗</p>
            </div>
        </div>
    );
};

export default QuickOrderWelcome;
