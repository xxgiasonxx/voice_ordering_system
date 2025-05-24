// SVG Icon as a React Component
const XIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"></path>
  </svg>
);

// Sample data for order items
// In a real application, this data would likely come from props, context, or a state management solution.
const orderItemsData = [
  { name: '炒飯', quantity: 1, price: '$10' },
  { name: '清潤的水', quantity: 1, price: '$2' },
  { name: '可樂', quantity: 1, price: '$2' },
  { name: '柳橘汁', quantity: 1, price: '$3' },
  { name: '果汁', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
  { name: '咖啡', quantity: 1, price: '$3' },
];

// Component for a single order item
const OrderItem = ({ name, quantity, price }: { name: string; quantity: number; price: string }) => (
  <div className="flex items-center gap-4 bg-slate-50 px-4 min-h-[72px] py-2 justify-between">
    <div className="flex flex-col justify-center overflow-hidden"> {/* Added overflow-hidden for line-clamp to work effectively with flex parents */}
      <p className="text-[#0d141c] text-base font-medium leading-normal line-clamp-1">{name}</p>
      <p className="text-[#49739c] text-sm font-normal leading-normal line-clamp-2">{quantity}</p>
    </div>
    <div className="shrink-0">
      <p className="text-[#0d141c] text-base font-normal leading-normal">{price}</p>
    </div>
  </div>
);

function OrderSummaryScreen() {
  // Notes for Vite + React + Tailwind CSS setup:
  // 1. Font links (Google Fonts) are typically placed in `public/index.html` or imported in `src/index.css`.
  // 2. The Tailwind CSS CDN script is replaced by installing Tailwind as a dev dependency and configuring it.
  // 3. `<title>` and favicon `<link>` go into `public/index.html`.
  // 4. The `line-clamp-*` classes require the `@tailwindcss/line-clamp` plugin.
  //    Install it: `npm install -D @tailwindcss/line-clamp`
  //    And add it to your `tailwind.config.js` plugins array: `require('@tailwindcss/line-clamp')`

  // Calculate total or other summary details if needed
  // For example:
  // const subtotal = orderItemsData.reduce((sum, item) => {
  //   return sum + parseFloat(item.price.substring(1)) * item.quantity;
  // }, 0);
  // const tax = subtotal * 0.05; // Example tax
  // const total = subtotal + tax;

  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-slate-50 justify-between group/design-root overflow-x-hidden"
      style={{ fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif' }}
    >
      {/* Main content area */}
      <div className="flex-grow overflow-y-auto"> {/* Added flex-grow and overflow-y-auto for scrollable content */}
        {/* Header */}
        <div className="flex items-center bg-slate-50 p-4 pb-2 justify-between sticky top-0 z-10"> {/* Made header sticky */}
          <div className="text-[#0d141c] flex size-12 shrink-0 items-center" data-icon="X" data-size="24px" data-weight="regular">
            {/* This X icon would typically have an onClick handler, e.g., to close a modal or navigate back */}
            <XIcon />
          </div>
          <h2 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center pr-12">訂單總覽</h2>
        </div>

        {/* Order Details Title */}
        <h2 className="text-[#0d141c] text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5">訂單明細</h2>

        {/* Order Items List */}
        {orderItemsData.map((item, index) => (
          <OrderItem key={index} name={item.name} quantity={item.quantity} price={item.price} />
        ))}
        
        {/* Special "Headline" item - its structure was different in the provided HTML */}
        <div className="flex items-center gap-4 bg-slate-50 px-4 min-h-[72px] py-2"> {/* Note: `justify-between` was missing here in original HTML */}
          <div className="flex flex-col justify-center overflow-hidden">
            <p className="text-[#0d141c] text-base font-medium leading-normal line-clamp-1">Headline</p>
            <p className="text-[#49739c] text-sm font-normal leading-normal line-clamp-2">1</p>
          </div>
          {/* Price was missing for this item in original HTML */}
        </div>
      </div>
      
      {/* Bottom Spacer (or potential footer area) */}
      <div> {/* This div ensures the spacer is at the bottom if content is short, or after scrollable content */}
        {/* Here you could add total summary, action buttons etc. For example:
        <div className="p-4 border-t border-slate-200">
          <div className="flex justify-between text-lg font-bold">
            <span>Total:</span>
            <span>${total.toFixed(2)}</span>
          </div>
          <button className="mt-4 w-full bg-[#0c7ff2] text-white py-3 rounded-xl font-bold">
            Proceed to Payment
          </button>
        </div>
        */}
        <div className="h-5 bg-slate-50"></div>
      </div>
    </div>
  );
}

export default OrderSummaryScreen;