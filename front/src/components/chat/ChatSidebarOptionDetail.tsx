interface ChatSidebarOptionDetailProps {
    showSidebar: boolean;
    setShowSidebar: React.Dispatch<React.SetStateAction<boolean>>;
    setShowAddUser: React.Dispatch<React.SetStateAction<boolean>>;
    setShowConfirm: React.Dispatch<React.SetStateAction<boolean>>;
  }
  
  const ChatSidebarOptionDetail = ({
    showSidebar,
    setShowSidebar,
    setShowAddUser,
    setShowConfirm,
  }: ChatSidebarOptionDetailProps) => {
    return (
      <div
        className={`fixed top-0 right-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 z-40 ${
          showSidebar ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="p-4 border-b flex justify-between items-center">
          <h3 className="text-lg font-semibold">Tùy chọn</h3>
          <button
            onClick={() => setShowSidebar(false)}
            className="text-gray-500 hover:text-gray-700 cursor-pointer"
          >
            ✕
          </button>
        </div>
        <div className="p-4">
          <p
            onClick={() => {setShowAddUser(true)}}
            className="mb-2 bg-blue-500 rounded p-1 cursor-pointer text-white"
          >
            Thêm thành viên
          </p>
          <p className="mb-2">Danh sách thành viên</p>
          <p
            onClick={()=>{setShowConfirm(true)}}
            className="mb-2 bg-red-500 rounded p-1 cursor-pointer text-white"
          >
            Rời nhóm
          </p>
        </div>
      </div>
    );
  };
  
  export default ChatSidebarOptionDetail;
  