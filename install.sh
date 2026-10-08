#!/usr/bin/env bash
# Travel Itinerary の skill を Claude Code・Codex・Kiro にインストールする。
#
#   curl -fsSL https://raw.githubusercontent.com/yoshimi-I/travel-itinerary/main/install.sh | bash
#   ./install.sh               # clone したリポジトリから入れる
#   ./install.sh --claude      # Claude Code だけ
#   ./install.sh --codex       # Codex だけ
#   ./install.sh --kiro        # Kiro だけ（--claude --kiro のように組み合わせも可）
#   ./install.sh --uninstall   # 削除する
#
# 環境変数:
#   TRAVEL_ITINERARY_REF   ダウンロードするブランチ・タグ（既定: main）
#   CLAUDE_CONFIG_DIR      Claude Code の設定ディレクトリ（既定: ~/.claude）
#   CODEX_SKILLS_DIR       Codex の skill ディレクトリ（既定: ~/.agents/skills）
#   KIRO_SKILLS_DIR        Kiro の skill ディレクトリ（既定: ~/.kiro/skills）
#   TRAVEL_ITINERARY_ARCHIVE_URL  ダウンロードする tar.gz の URL（ミラーやテスト用）

set -euo pipefail

REPO="yoshimi-I/travel-itinerary"
SKILL="travel-itinerary"
MARKER=".installed-by-travel-itinerary"

# パイプで渡されたときに、途中までダウンロードした状態で実行されないよう、全体を関数にしている
main() {
  local ref="${TRAVEL_ITINERARY_REF:-main}"
  local claude_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
  local codex_dir="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
  local kiro_dir="${KIRO_SKILLS_DIR:-$HOME/.kiro/skills}"
  local want_claude=0 want_codex=0 want_kiro=0 uninstall=0

  while [ $# -gt 0 ]; do
    case "$1" in
      --claude) want_claude=1 ;;
      --codex) want_codex=1 ;;
      --kiro) want_kiro=1 ;;
      --uninstall) uninstall=1 ;;
      -h | --help) usage; return 0 ;;
      *) error "知らないオプションです: ${1}（--help で使い方を表示）" ;;
    esac
    shift
  done

  # どれも指定されなければ全部に入れる
  if [ $((want_claude + want_codex + want_kiro)) -eq 0 ]; then
    want_claude=1 want_codex=1 want_kiro=1
  fi
  local targets=()
  [ "$want_claude" -eq 1 ] && targets+=("Claude Code|$claude_dir/$SKILL")
  [ "$want_codex" -eq 1 ] && targets+=("Codex|$codex_dir/$SKILL")
  [ "$want_kiro" -eq 1 ] && targets+=("Kiro|$kiro_dir/$SKILL")

  if [ "$uninstall" -eq 1 ]; then
    local t
    for t in "${targets[@]}"; do remove "${t%%|*}" "${t#*|}"; done
    return 0
  fi

  local tmp="" src
  src="$(local_source || true)"
  if [ -z "$src" ]; then
    tmp="$(mktemp -d)"
    # shellcheck disable=SC2064
    trap "rm -rf '$tmp'" EXIT
    src="$(download "$ref" "$tmp")"
  fi

  local t
  for t in "${targets[@]}"; do install_to "${t%%|*}" "${t#*|}" "$src"; done

  if ! command -v python3 >/dev/null 2>&1; then
    warn "python3 が見つかりません。なくても使えますが、入れておくとしおりの作成が安定します。"
  fi

  info ""
  info "インストールしました。しおりを作りたいフォルダでエージェントを起動して、次のように話しかけてください。"
  [ "$want_claude" -eq 1 ] && info "  Claude Code: /travel-itinerary"
  # shellcheck disable=SC2016
  [ "$want_codex" -eq 1 ] && info '  Codex:       $travel-itinerary'
  [ "$want_kiro" -eq 1 ] && info "  Kiro:        /travel-itinerary"
  info "（「旅のしおりを作りたい」と話しかけるだけでも始まります）"
}

usage() {
  cat <<'EOF'
使い方: install.sh [--claude] [--codex] [--kiro] [--uninstall]

  オプションなし  Claude Code・Codex・Kiro のすべてにインストール（もう一度実行すると更新）
  --claude        Claude Code に入れる
  --codex         Codex に入れる
  --kiro          Kiro に入れる（組み合わせて指定できます）
  --uninstall     削除する

環境変数:
  TRAVEL_ITINERARY_REF   ダウンロードするブランチ・タグ（既定: main）
  CLAUDE_CONFIG_DIR      Claude Code の設定ディレクトリ（既定: ~/.claude）
  CODEX_SKILLS_DIR       Codex の skill ディレクトリ（既定: ~/.agents/skills）
  KIRO_SKILLS_DIR        Kiro の skill ディレクトリ（既定: ~/.kiro/skills）
EOF
}

info() { printf '%s\n' "$*"; }
warn() { printf '注意: %s\n' "$*" >&2; }
error() { printf 'エラー: %s\n' "$*" >&2; exit 1; }

# clone したリポジトリの中から実行された場合は、そのファイルを使う
local_source() {
  local self="${BASH_SOURCE[0]:-}"
  if [ -z "$self" ] || [ ! -f "$self" ]; then return 1; fi
  local dir
  dir="$(cd "$(dirname "$self")" && pwd)"
  [ -f "$dir/.agents/skills/$SKILL/SKILL.md" ] || return 1
  printf '%s\n' "$dir/.agents/skills/$SKILL"
}

download() {
  local ref="$1" tmp="$2"
  local url="${TRAVEL_ITINERARY_ARCHIVE_URL:-https://codeload.github.com/$REPO/tar.gz/$ref}"
  command -v curl >/dev/null 2>&1 || error "curl が必要です"
  command -v tar >/dev/null 2>&1 || error "tar が必要です"
  info "ダウンロードしています: $REPO@$ref" >&2
  curl -fsSL "$url" -o "$tmp/src.tar.gz" || error "ダウンロードに失敗しました: $url"
  tar -xzf "$tmp/src.tar.gz" -C "$tmp"
  local found
  found="$(find "$tmp" -mindepth 4 -maxdepth 4 -type d -path "*/.agents/skills/$SKILL" | head -n 1)"
  if [ -z "$found" ] || [ ! -f "$found/SKILL.md" ]; then
    error "ダウンロードしたファイルに skill が見つかりません"
  fi
  printf '%s\n' "$found"
}

# 自分で入れたもの以外は上書き・削除しない
owned_or_absent() {
  local dest="$1"
  [ ! -e "$dest" ] || [ -f "$dest/$MARKER" ]
}

install_to() {
  local name="$1" dest="$2" src="$3"
  owned_or_absent "$dest" ||
    error "$dest には別の skill があるため、上書きしません。不要なら削除してからもう一度実行してください。"
  mkdir -p "$(dirname "$dest")"
  local staging="$dest.tmp.$$"
  rm -rf "$staging"
  mkdir -p "$staging"
  local item
  for item in SKILL.md VERSION references assets scripts; do
    [ -e "$src/$item" ] && cp -R "$src/$item" "$staging/"
  done
  find "$staging" -name '__pycache__' -type d -prune -exec rm -rf {} +
  {
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [ -f "$src/VERSION" ]; then printf 'version=%s\n' "$(head -n 1 "$src/VERSION")"; fi
  } >"$staging/$MARKER"
  rm -rf "$dest"
  mv "$staging" "$dest"
  info "$name: $dest"
}

remove() {
  local name="$1" dest="$2"
  if [ ! -e "$dest" ]; then
    info "$name: インストールされていません"
    return 0
  fi
  owned_or_absent "$dest" || error "$dest はこのスクリプトで入れたものではないため、削除しません。"
  rm -rf "$dest"
  info "$name: 削除しました（${dest}）"
}

main "$@"
