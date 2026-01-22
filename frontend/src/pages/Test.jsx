import Dropzone from "@/components/custom/Dropzone";
import { Button } from "@/components/ui/button";
import axios from "axios";
export default function Test() {
  function testConnection() {
    console.log("It's time!");
    axios
      .get("http://127.0.0.1:8000/api/user-profiles")
      .then((response) => console.log(response.data))
      .catch((error) => console.error(error));
  }
  return (
    <>
      <Dropzone title="Cool test" />
      <Button className="hover:cursor-pointer" onClick={testConnection}>
        Chicken
      </Button>
    </>
  );
}
