interface AddUserModalProps {
    showAddUser: boolean;
    setShowAddUser: React.Dispatch<React.SetStateAction<boolean>>;
}

const AddUserModal = ({ showAddUser, setShowAddUser }: AddUserModalProps) => {
    return (
        <div>
            {showAddUser && (
                <div className="fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm z-50">
                    <div className="bg-white rounded-lg shadow-lg p-6 w-80">
                        <h2 className="text-lg font-semibold mb-4">Thành viên sẽ thêm</h2>
                        <input
                            type="text"
                            placeholder="UserId"
                            className="border rounded-lg px-4 py-2 flex-1"
                        />
                        <div className="flex justify-end py-2 gap-3">
                            <button
                                onClick={() => setShowAddUser(false)}
                                className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 cursor-pointer"
                            >
                                Hủy
                            </button>
                            <button
                                onClick={() => {

                                }}
                                className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-red-600 cursor-pointer"
                            >
                                Xác nhận
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
export default AddUserModal;
