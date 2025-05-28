import { createBrowserRouter } from "react-router-dom";
import Error from "../pages/Error";
import Home from "../pages/Home";
import Choice from "../pages/Choice";
import Menu from "../pages/Menu";
import VoiceOrder from "../pages/VoiceOrder";
import OrderState from "../pages/OrderState"
import OrderView from "../pages/OrderView";
import Payment from "../pages/Payment";
import SpeechToText from "../pages/test";
// import { InitOrderState } from "../protect/InitOrderState";

export const router = createBrowserRouter([

  {
    path: "/",
    element: <Home />,
    errorElement: <Error />,
  },
  {
    path: "/choice",
    element: <Choice />, // Assuming Home is the welcome page
    errorElement: <Error />,
  },
  {
    path: "/menu",
    element: <Menu />,
    errorElement: <Error />,
  },
  {
    path: "/voiceorder",
    element: <VoiceOrder />,
    errorElement: <Error />,
  },
  {
    path: "/orderstate",
    element: <OrderState />,
    errorElement: <Error />,
  },
  {
    path: "/orderview",
    element: <OrderView />,
    errorElement: <Error />,
  },
  {
    path: "/payment",
    element: <Payment />,
    errorElement: <Error />,
  },
  {
    path: "/test",
    element: <SpeechToText />,
    errorElement: <Error />,
  }
]);