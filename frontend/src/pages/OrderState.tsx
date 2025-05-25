import { ArrowLeftIcon, CheckIcon, HouseIcon, ReceiptIcon, MagnifyingGlassIcon, UserIcon } from "../components/Icon";
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