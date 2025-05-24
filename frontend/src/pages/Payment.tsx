import { useState } from 'react';

// Define types for better code clarity and safety
interface PaymentOption {
  id: string;
  value: string;
  label: string;
}

interface OrderSummaryValues {
  subtotal: number;
  deliveryFee: number;
  total: number;
}

// SVG Icon Component
const ArrowLeftIcon: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" viewBox="0 0 256 256">
    <path d="M224,128a8,8,0,0,1-8,8H59.31l58.35,58.34a8,8,0,0,1-11.32,11.32l-72-72a8,8,0,0,1,0-11.32l72-72a8,8,0,0,1,11.32,11.32L59.31,120H216A8,8,0,0,1,224,128Z"></path>
  </svg>
);

const PaymentScreen: React.FC = () => {
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>("credit-card"); // Default to 'credit-card'

  const paymentOptions: PaymentOption[] = [
    { id: "credit-card-radio", value: "credit-card", label: "Credit card" },
    { id: "cod-radio", value: "cash-on-delivery", label: "Cash on delivery" },
  ];

  // Example order summary data. In a real app, this would likely come from props or context.
  const orderSummary: OrderSummaryValues = {
    subtotal: 12.99,
    deliveryFee: 2.00,
    total: 14.99,
  };

  const handlePaymentMethodChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedPaymentMethod(event.target.value);
  };

  // CSS custom property for the radio button dot.
  // Note: The data URL is long; ensure it's correctly formatted.
  const radioDotSvgUrl = "url('data:image/svg+xml,%3csvg viewBox=%270 0 16 16%27 fill=%27rgb(12,127,242)%27 xmlns=%27http://www.w3.org/2000/svg%27%3e%3ccircle cx=%278%27 cy=%278%27 r=%273%27/%3e%3c/svg%3e')";

  const rootStyle: React.CSSProperties = {
    '--radio-dot-svg': radioDotSvgUrl,
    fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif',
  } as React.CSSProperties; // Added type assertion for custom property

  // Notes for Vite + React + Tailwind CSS + TypeScript setup:
  // 1. Font links (Google Fonts) are typically placed in `public/index.html` or imported in `src/index.css`.
  // 2. The Tailwind CSS CDN script is replaced by installing Tailwind as a dev dependency and configuring it.
  // 3. `<title>` and favicon `<link>` go into `public/index.html`.
  // 4. Ensure Tailwind's JIT mode correctly picks up `checked:bg-[image:--radio-dot-svg]`.
  //    If not, you might need to define this custom utility or ensure the CSS variable is globally accessible
  //    and understood by Tailwind. The inline style definition on the root div should make it available.

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
            {/* This icon would typically have an onClick handler for navigation */}
            <ArrowLeftIcon />
          </div>
          <h2 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center pr-12">Payment</h2>
        </div>

        {/* Payment Method Section */}
        <h3 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] px-4 pb-2 pt-4">Payment method</h3>
        <div className="flex flex-col gap-3 p-4">
          {paymentOptions.map((option) => (
            <label
              key={option.id}
              htmlFor={option.id}
              className="flex items-center gap-4 rounded-xl border border-solid border-[#cedbe8] p-[15px] flex-row-reverse cursor-pointer hover:border-[#0c7ff2]"
            >
              <input
                type="radio"
                id={option.id}
                name="paymentMethodGroup" // Grouping radio buttons
                value={option.value}
                checked={selectedPaymentMethod === option.value}
                onChange={handlePaymentMethodChange}
                className="h-5 w-5 border-2 border-[#cedbe8] bg-transparent text-transparent checked:border-[#0c7ff2] checked:bg-[image:var(--radio-dot-svg)] focus:outline-none focus:ring-0 focus:ring-offset-0 checked:focus:border-[#0c7ff2]"
              />
              <div className="flex grow flex-col">
                <p className="text-[#0d141c] text-sm font-medium leading-normal">{option.label}</p>
              </div>
            </label>
          ))}
        </div>

        {/* Order Summary Section */}
        <h3 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] px-4 pb-2 pt-4">Order summary</h3>
        <div className="p-4">
          <div className="flex justify-between gap-x-6 py-2">
            <p className="text-[#49739c] text-sm font-normal leading-normal">Subtotal</p>
            <p className="text-[#0d141c] text-sm font-normal leading-normal text-right">${orderSummary.subtotal.toFixed(2)}</p>
          </div>
          <div className="flex justify-between gap-x-6 py-2">
            <p className="text-[#49739c] text-sm font-normal leading-normal">Delivery fee</p>
            <p className="text-[#0d141c] text-sm font-normal leading-normal text-right">${orderSummary.deliveryFee.toFixed(2)}</p>
          </div>
          <div className="flex justify-between gap-x-6 py-2">
            <p className="text-[#49739c] text-sm font-normal leading-normal">Total</p>
            <p className="text-[#0d141c] text-sm font-normal leading-normal text-right">${orderSummary.total.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* Footer / Action Button Area */}
      <div>
        <div className="flex px-4 py-3">
          <button
            className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-5 flex-1 bg-[#0c7ff2] text-slate-50 text-base font-bold leading-normal tracking-[-0.015em] hover:bg-blue-600 active:bg-blue-700"
            // onClick handler for payment submission would go here
          >
            <span className="truncate">Pay ${orderSummary.total.toFixed(2)}</span>
          </button>
        </div>
        <div className="h-5 bg-slate-50"></div> {/* Bottom spacer */}
      </div>
    </div>
  );
};

export default PaymentScreen;