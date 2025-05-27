import icon from '@/assets/Logo.png';
import Header from '@/components/Header';

const Loading = () => {
    return (
        <div
            className="relative flex h-screen flex-col bg-white justify-between overflow-x-hidden"
            style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
        >
            <Header to="/" name="點餐系統" />

            {/* Main Content */}
            <div className="flex-1 flex flex-col justify-center items-center px-6">
                {/* Logo Section */}
                <div className="text-center mb-8">
                    <div className="mb-6">
                        <img src={icon} alt="Logo" className="w-24 h-24 mx-auto rounded-2xl shadow-lg border-gray-300" />
                    </div>
                    <h1 className="text-black text-3xl font-bold mb-3">載入中...</h1>
                    <p className="text-black text-lg">請稍後，系統正在準備中</p>
                </div>

                {/* Loading Animation */}
                <div className="flex items-center justify-center mb-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-[#50b4ea]"></div>
                </div>

                {/* Progress Dots */}
                <div className="flex space-x-2">
                    <div className="w-3 h-3 bg-[#50b4ea] rounded-full animate-bounce"></div>
                    <div className="w-3 h-3 bg-[#50b4ea] rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-3 h-3 bg-[#50b4ea] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-6 text-center">
                <p className="text-black text-sm">正在為您準備最佳的點餐體驗</p>
            </div>
        </div>
    );
};

export default Loading;