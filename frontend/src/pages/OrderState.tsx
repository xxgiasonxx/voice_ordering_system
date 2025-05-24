// ## Type Definitions
// -----------------------------------------------------------------------------

interface OrderStatusStepData {
  id: string;
  label: string;
  isCompleted: boolean; // To control icon and line color if needed in the future
  // Add other properties like timestamp if necessary
}

interface NavItemData {
  id: string;
  label: string;
  href: string;
  icon: React.FC<React.SVGProps<SVGSVGElement>>; // Icon component
  isActive: boolean;
  iconWeight?: 'regular' | 'fill'; // To match the original HTML data attributes
}

interface StatusStepProps extends OrderStatusStepData {
  isFirst: boolean;
  isLast: boolean;
}


// ## SVG Icon Components
// -----------------------------------------------------------------------------

const ArrowLeftIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
    <path d="M224,128a8,8,0,0,1-8,8H59.31l58.35,58.34a8,8,0,0,1-11.32,11.32l-72-72a8,8,0,0,1,0-11.32l72-72a8,8,0,0,1,11.32,11.32L59.31,120H216A8,8,0,0,1,224,128Z"></path>
  </svg>
);

const CheckIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
    <path d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"></path>
  </svg>
);

const HouseIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
    <path d="M218.83,103.77l-80-75.48a1.14,1.14,0,0,1-.11-.11,16,16,0,0,0-21.53,0l-.11.11L37.17,103.77A16,16,0,0,0,32,115.55V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V160h32v48a16,16,0,0,0,16,16h48a16,16,0,0,0,16-16V115.55A16,16,0,0,0,218.83,103.77ZM208,208H160V160a16,16,0,0,0-16-16H112a16,16,0,0,0-16,16v48H48V115.55l.11-.1L128,40l79.9,75.43.11.1Z"></path>
  </svg>
);

const ReceiptIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
    <path d="M216,40H40A16,16,0,0,0,24,56V208a8,8,0,0,0,11.58,7.15L64,200.94l28.42,14.21a8,8,0,0,0,7.16,0L128,200.94l28.42,14.21a8,8,0,0,0,7.16,0L192,200.94l28.42,14.21A8,8,0,0,0,232,208V56A16,16,0,0,0,216,40ZM176,144H80a8,8,0,0,1,0-16h96a8,8,0,0,1,0,16Zm0-32H80a8,8,0,0,1,0-16h96a8,8,0,0,1,0,16Z"></path>
  </svg>
);

const MagnifyingGlassIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
    <path d="M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z"></path>
  </svg>
);

const UserIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256" {...props}>
    <path d="M230.92,212c-15.23-26.33-38.7-45.21-66.09-54.16a72,72,0,1,0-73.66,0C63.78,166.78,40.31,185.66,25.08,212a8,8,0,1,0,13.85,8c18.84-32.56,52.14-52,89.07-52s70.23,19.44,89.07,52a8,8,0,1,0,13.85-8ZM72,96a56,56,0,1,1,56,56A56.06,56.06,0,0,1,72,96Z"></path>
  </svg>
);


// ## Sub-Components
// -----------------------------------------------------------------------------

const StatusStep: React.FC<StatusStepProps> = ({ label, isCompleted, isFirst, isLast }) => {
  // In a real app, isCompleted would determine the icon and color
  const iconColor = isCompleted ? "text-[#0d141c]" : "text-[#cedbe8]"; // Example for future use
  const lineColor = isCompleted ? "bg-[#0d141c]" : "bg-[#cedbe8]";   // Example for future use

  return (
    <>
      <div className={`flex flex-col items-center gap-1 ${isLast ? 'pb-3' : ''} ${isFirst ? 'pt-3' : ''}`}>
        {!isFirst && <div className={`w-[1.5px] ${lineColor} h-2`}></div>}
        <div className={iconColor} data-icon="Check" data-size="24px" data-weight="regular">
          <CheckIcon />
        </div>
        {!isLast && <div className={`w-[1.5px] ${lineColor} h-2 grow`}></div>}
      </div>
      <div className="flex flex-1 flex-col pt-3 pb-5">
        <p className="text-[#0d141c] text-base font-medium leading-normal">{label}</p>
      </div>
    </>
  );
};

const BottomNavItem: React.FC<NavItemData> = ({ label, href, icon: Icon, isActive, iconWeight }) => {
  const textColor = isActive ? "text-[#0d141c]" : "text-[#49739c]";
  return (
    <a className={`just flex flex-1 flex-col items-center justify-end gap-1 ${isActive ? 'rounded-full' : ''} ${textColor}`} href={href}>
      <div className={`${textColor} flex h-8 items-center justify-center`} data-size="24px" data-weight={iconWeight || 'regular'}>
        <Icon />
      </div>
      <p className={`${textColor} text-xs font-medium leading-normal tracking-[0.015em]`}>{label}</p>
    </a>
  );
};


// ## Main Component: OrderStatusScreen
// -----------------------------------------------------------------------------
const OrderStatusScreen: React.FC = () => {
  // Sample data for order status steps.
  // In a real app, this would come from props or state, and isCompleted would be dynamic.
  const statusStepsData: OrderStatusStepData[] = [
    { id: "s1", label: "已接單", isCompleted: true },
    { id: "s2", label: "製作中", isCompleted: true },
    { id: "s3", label: "準備完成", isCompleted: true },
    { id: "s4", label: "配送中", isCompleted: true },
    // Example of a future step:
    // { id: "s5", label: "已送達", isCompleted: false },
  ];

  const navItemsData: NavItemData[] = [
    { id: "nav1", label: "首頁", href: "#", icon: HouseIcon, isActive: false },
    { id: "nav2", label: "訂單", href: "#", icon: ReceiptIcon, isActive: true, iconWeight: 'fill' },
    { id: "nav3", label: "搜尋", href: "#", icon: MagnifyingGlassIcon, isActive: false },
    { id: "nav4", label: "我的", href: "#", icon: UserIcon, isActive: false },
  ];

  const rootStyle: React.CSSProperties = {
    fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif',
  };

  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-slate-50 justify-between group/design-root overflow-x-hidden"
      style={rootStyle}
    >
      {/* Main content area */}
      <div className="flex-grow">
        {/* Header */}
        <div className="flex items-center bg-slate-50 p-4 pb-2 justify-between sticky top-0 z-10">
          <div className="text-[#0d141c] flex size-12 shrink-0 items-center" data-icon="ArrowLeft" data-size="24px" data-weight="regular">
            <ArrowLeftIcon />
          </div>
          <h2 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center pr-12">訂單狀態</h2>
        </div>

        {/* Order Status Tracker */}
        <div className="grid grid-cols-[40px_1fr] gap-x-2 px-4">
          {statusStepsData.map((step, index) => (
            <StatusStep
              key={step.id}
              {...step}
              isFirst={index === 0}
              isLast={index === statusStepsData.length - 1}
            />
          ))}
        </div>
      </div>

      {/* Bottom Navigation Area */}
      <div>
        <div className="flex gap-2 border-t border-[#e7edf4] bg-slate-50 px-4 pb-3 pt-2">
          {navItemsData.map((item) => (
            <BottomNavItem key={item.id} {...item} />
          ))}
        </div>
        <div className="h-5 bg-slate-50"></div> {/* Bottom spacer */}
      </div>
    </div>
  );
};

export default OrderStatusScreen;

// Notes for Vite + React + Tailwind CSS + TypeScript setup:
// 1. Font links (Google Fonts) are typically placed in `public/index.html` or imported in `src/index.css`.
// 2. The Tailwind CSS CDN script is replaced by installing Tailwind as a dev dependency and configuring it.
// 3. `<title>` and favicon `<link>` go into `public/index.html`.