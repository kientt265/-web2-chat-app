interface ConfirmLeaveModalProps {
    showConfirm: boolean;
    setShowConfirm: React.Dispatch<React.SetStateAction<boolean>>;
    callRejectSecretConversation: () => void;

}
const ConfirmLeaveModal = ({showConfirm, setShowConfirm, callRejectSecretConversation}: ConfirmLeaveModalProps) => {
    return (
        <div>
            {showConfirm && (
                <div className="fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm z-50">
                    <div className="bg-white rounded-lg shadow-lg p-6 w-80">
                        <h2 className="text-lg font-semibold mb-4">Xác nhận</h2>
                        <p className="text-sm text-gray-600 mb-6">
                            Bạn có chắc chắn muốn rời nhóm không?
                        </p>
                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setShowConfirm(false)}
                                className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 cursor-pointer"
                            >
                                Hủy
                            </button>
                            <button
                                onClick={() => {
                                    callRejectSecretConversation();
                                    setShowConfirm(false);
                                }}
                                className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600 cursor-pointer"
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

export default ConfirmLeaveModal;