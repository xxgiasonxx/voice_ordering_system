import icon from '@/assets/icon.png';
import { Link } from 'react-router-dom';

const ArrowLeftIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
        <path d="M224,128a8,8,0,0,1-8,8H59.31l58.35,58.34a8,8,0,0,1-11.32,11.32l-72-72a8,8,0,0,1,0-11.32l72-72a8,8,0,0,1,11.32,11.32L59.31,120H216A8,8,0,0,1,224,128Z"></path>
    </svg>
);

const MicIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2Z" fill="currentColor"/>
        <path d="M19 11C19 15.42 15.42 19 11 19V21H13V23H11H9V21H11V19C6.58 19 3 15.42 3 11H5C5 14.31 7.69 17 11 17C14.31 17 17 14.31 17 11H19Z" fill="currentColor"/>
    </svg>
);

const MenuIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 18H21V16H3V18ZM3 13H21V11H3V13ZM3 6V8H21V6H3Z" fill="currentColor"/>
    </svg>
);

const QuickOrderWelcome = () => {
    return (
        <div
            className="relative flex h-screen flex-col bg-white justify-between overflow-x-hidden"
            style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
        >
            {/* Header */}
            <div className="flex items-center bg-white p-4 pb-3 justify-between sticky top-0 z-10 shadow-sm border-b border-gray-200">
                <div className="text-black flex size-12 shrink-0 items-center justify-center rounded-full hover:bg-gray-100 transition-colors">
                    <Link to="/">
                        <ArrowLeftIcon />
                    </Link>
                </div>
                <h2 className="text-black text-xl font-bold tracking-tight flex-1 text-center pr-12">選擇點餐方式</h2>
            </div>

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
