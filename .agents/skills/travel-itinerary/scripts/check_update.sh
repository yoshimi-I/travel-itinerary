#!/bin/sh
# 新しいバージョンが公開されていれば知らせる。何もなければ何も出力しない。
#
# - install.sh で入れた skill のときだけ確認する（clone したリポジトリでは git pull で更新する）
# - 確認は 1 日 1 回まで。ネットにつながらない・時間がかかるときは、何もせずに終わる
# - TRAVEL_ITINERARY_NO_UPDATE_CHECK=1 で確認しない
#
# 環境変数（テスト用）:
#   TRAVEL_ITINERARY_VERSION_URL  最新の VERSION を取ってくる URL

set -u

[ "${TRAVEL_ITINERARY_NO_UPDATE_CHECK:-}" = "1" ] && exit 0

skill_dir=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd) || exit 0
[ -f "${skill_dir}/.installed-by-travel-itinerary" ] || exit 0
[ -f "${skill_dir}/VERSION" ] || exit 0
command -v curl >/dev/null 2>&1 || exit 0

stamp="${skill_dir}/.last-update-check"
now=$(date +%s)
if [ -f "${stamp}" ]; then
  last=$(cat "${stamp}" 2>/dev/null || echo 0)
  case "${last}" in *[!0-9]* | "") last=0 ;; esac
  [ $((now - last)) -lt 86400 ] && exit 0
fi
echo "${now}" >"${stamp}" 2>/dev/null || true

url="${TRAVEL_ITINERARY_VERSION_URL:-https://raw.githubusercontent.com/yoshimi-I/travel-itinerary/main/.agents/skills/travel-itinerary/VERSION}"
latest=$(curl -fsSL --max-time 3 "${url}" 2>/dev/null | head -n 1 | tr -d '[:space:]') || exit 0
current=$(head -n 1 "${skill_dir}/VERSION" | tr -d '[:space:]')

valid() { printf '%s' "$1" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; }
if ! valid "${latest}" || ! valid "${current}"; then exit 0; fi

# latest が current より新しければ 0 を返す
newer=$(awk -v a="${latest}" -v b="${current}" 'BEGIN {
  split(a, x, "."); split(b, y, ".")
  for (i = 1; i <= 3; i++) { if (x[i] + 0 > y[i] + 0) { print 1; exit } if (x[i] + 0 < y[i] + 0) { print 0; exit } }
  print 0
}')
[ "${newer}" = "1" ] || exit 0

echo "Travel Itinerary の新しいバージョン（${latest}）があります。今のバージョンは ${current} です。"
echo "更新するには: curl -fsSL https://raw.githubusercontent.com/yoshimi-I/travel-itinerary/main/install.sh | bash"
