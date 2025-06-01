import { useEffect, useState } from 'react';
import { ArrowLeftIcon } from '@/components/Icon';
import { Link } from 'react-router-dom';
import axios from 'axios';

// Define types for better code clarity and safety
interface PaymentOption {
  id: string;
  value: string;
  label: string;
}

interface OrderItem {
  id: string;
  item_id: number | string;
  class: string;
  name: string;
  unitPrice: number;
  subtotal: number;
  quantity: number;
  customization: {
    cus_price: number;
    note: string;
  };
}

interface OrderSummaryValues {
  items: OrderItem[];
  order_id?: string;
  order_time?: string;
  order_type?: string;
  payment?:{
    method?: string;
    status?: string;
  };
  subtotal?: number;
  deliveryFee?: number;
  total_price?: number;
}

const PaymentScreen: React.FC = () => {
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>("counter-payment"); // Default to 'counter-payment'
  const [orderSummary, setOrderSummary] = useState<OrderSummaryValues>({
    items: [],
    subtotal: 0,
    deliveryFee: 0,
    total_price: 0,
  });

  const fetchOrderSummary = async () => {
    const baseUrl: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    try {
      const response = await axios.get(`${baseUrl}/see_order`, {
        withCredentials: true, // Ensure cookies are sent with the request
      });

      if (response.status === 200) {
        console.log("Order summary fetched successfully:", response.data);
        setOrderSummary(response.data.order_state);
      } else {
        console.error("Failed to fetch order summary:", response.data.msg);
      }
    } catch (error) {
      console.error("Error fetching order summary:", error);
    }
  };

  useEffect(() => {
    fetchOrderSummary();
  }, []); // Fetch order summary on component mount

  const paymentOptions: PaymentOption[] = [
    { id: "counter-payment-radio", value: "counter-payment", label: "櫃台結帳" },
    { id: "electronic-payment-radio", value: "electronic-payment", label: "電子支付" },
  ];


  const handlePaymentMethodChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedPaymentMethod(event.target.value);
  };

  const handlePaymentSubmission = async () => {
    // Handle payment submission logic here
    const baseUrl: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const paymentUrl = `${baseUrl}/submit_payment`;
    const response = await axios.post(paymentUrl, {}, {
      withCredentials: true, // Ensure cookies are sent with the request
    });

    if (response.status === 200) {
      // Handle successful payment submission
      console.log("Payment submitted successfully:", response.data.msg);
      // Redirect to order view or confirmation page
      alert("感謝您的送出訂單!");
      window.location.href = "/"; // Redirect to order view
    } else {
      // Handle error in payment submission
      console.error("Payment submission failed:", response.data.msg);
    }

    const response2 = await axios.post(`${baseUrl}/clean_cookie`, {
      withCredentials: true, // Ensure cookies are sent with the request
    });

    if (response2.status === 200) {
      console.log("Cookies cleaned successfully:", response2.data.msg);
    } else {
      console.error("Failed to clean cookies:", response2.data.msg);
    }
  };

  // CSS custom property for the radio button dot.
  // Note: The data URL is long; ensure it's correctly formatted.
  const radioDotSvgUrl = "url('data:image/svg+xml,%3csvg viewBox=%270 0 16 16%27 fill=%27rgb(12,127,242)%27 xmlns=%27http://www.w3.org/2000/svg%27%3e%3ccircle cx=%278%27 cy=%278%27 r=%273%27/%3e%3c/svg%3e')";

  const rootStyle: React.CSSProperties = {
    '--radio-dot-svg': radioDotSvgUrl,
    fontFamily: '"Plus Jakarta Sans", "Noto Sans", sans-serif',
  } as React.CSSProperties; // Added type assertion for custom property

  return (
    <div
      className="relative flex size-full min-h-screen flex-col bg-slate-50 justify-between group/design-root overflow-x-hidden"
      style={rootStyle}
    >
      {/* Main content area */}
      <div className="flex-grow px-4 sm:px-6 lg:px-8 max-w-md mx-auto w-full">
        {/* Header */}
        <div className="flex items-center bg-slate-50 py-6 pb-4 justify-between sticky top-0 z-10">
          <div className="text-[#0d141c] flex size-12 shrink-0 items-center" data-icon="ArrowLeft" data-size="24px" data-weight="regular">
            {/* This icon would typically have an onClick handler for navigation */}
            <Link
              to="/orderview"
            >
              <ArrowLeftIcon />
            </Link>
          </div>
          <h2 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center pr-12">付款</h2>
        </div>

        {/* Payment Method Section */}
        <div className="mb-8">
          <h3 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] pb-4 pt-2">付款方式</h3>
          <div className="flex flex-col gap-4">
            {paymentOptions.map((option) => (
              <label
                key={option.id}
                htmlFor={option.id}
                className="flex items-center gap-4 rounded-xl border border-solid border-[#cedbe8] p-4 flex-row-reverse cursor-pointer hover:border-[#0c7ff2] transition-colors"
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
        </div>

        {/* Order Summary Section */}
        <div className="mb-8">
          <h3 className="text-[#0d141c] text-lg font-bold leading-tight tracking-[-0.015em] pb-4 pt-2">訂單摘要</h3>
          <div className="bg-white rounded-xl p-6 border border-[#cedbe8]">
            {/* Order Items */}
            {orderSummary.items?.map((item) => (
              <div key={item.id} className="flex justify-between gap-x-6 py-3">
                <div className="flex-1">
                  <p className="text-[#0d141c] text-sm font-medium leading-normal">
                    {item.class} - {item.name} x{item.quantity}
                  </p>
                  {item.customization.note !== "無" && (
                    <p className="text-[#49739c] text-xs font-normal leading-normal">備註: {item.customization.note}</p>
                  )}
                </div>
                <p className="text-[#0d141c] text-sm font-normal leading-normal text-right">${item.subtotal}</p>
              </div>
            ))}
            
            <div className="border-t border-[#cedbe8] my-3"></div>
            {orderSummary.subtotal && (
            <div className="flex justify-between gap-x-6 py-3">
              <p className="text-[#49739c] text-sm font-normal leading-normal">小計</p>
              <p className="text-[#0d141c] text-sm font-normal leading-normal text-right">${orderSummary.subtotal}</p>
            </div>
            )}
            <div className="border-t border-[#cedbe8] my-3"></div>
            <div className="flex justify-between gap-x-6 py-3">
              <p className="text-[#0d141c] text-base font-bold leading-normal">總計</p>
              <p className="text-[#0d141c] text-base font-bold leading-normal text-right">${orderSummary.total_price}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / Action Button Area */}
      <div className="px-4 sm:px-6 lg:px-8 max-w-md mx-auto w-full">
        <div className="flex py-6">
          <button
            className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-14 px-6 flex-1 bg-[#0c7ff2] text-slate-50 text-base font-bold leading-normal tracking-[-0.015em] hover:bg-blue-600 active:bg-blue-700 transition-colors shadow-lg"
            // onClick handler for payment submission would go here
            onClick={handlePaymentSubmission}
          >
            <span className="truncate">
              {selectedPaymentMethod === 'counter-payment' ? '確認櫃台結帳' : '電子支付'} ${orderSummary.total_price}
            </span>
          </button>
        </div>
        <div className="h-6 bg-slate-50"></div> {/* Bottom spacer */}
      </div>
    </div>
  );
};

export default PaymentScreen;
