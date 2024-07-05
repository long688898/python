def generate_links(argo_domain):
    meta_info = subprocess.run(['curl', '-s', 'https://speed.cloudflare.com/meta'], capture_output=True, text=True)
    meta_info = meta_info.stdout.split('"')
    ISP = f"{meta_info[25]}-{meta_info[17]}".replace(' ', '_').strip()

    time.sleep(2)
    VMESS = {"v": "2", "ps": f"{NAME}-{ISP}", "add": CFIP, "port": CFPORT, "id": UUID, "aid": "0", "scy": "none", "net": "ws", "type": "none", "host": argo_domain, "path": "/vmess?ed=2048", "tls": "tls", "sni": argo_domain, "alpn": ""}
 
    list_txt = f"""
vless://{UUID}@{CFIP}:{CFPORT}?encryption=none&security=tls&sni={argo_domain}&type=ws&host={argo_domain}&path=%2Fvless%3Fed%3D2048#{NAME}-{ISP}
  
vmess://{ base64.b64encode(json.dumps(VMESS).encode('utf-8')).decode('utf-8')}

trojan://{UUID}@{CFIP}:{CFPORT}?security=tls&sni={argo_domain}&type=ws&host={argo_domain}&path=%2Ftrojan%3Fed%3D2048#{NAME}-{ISP}
    """
    
    with open(os.path.join(FILE_PATH, 'list.txt'), 'w', encoding='utf-8') as list_file:
        list_file.write(list_txt)

    sub_txt = base64.b64encode(list_txt.encode('utf-8')).decode('utf-8')
    with open(os.path.join(FILE_PATH, 'sub.txt'), 'w', encoding='utf-8') as sub_file:
        sub_file.write(sub_txt)
        
    try:
        with open(os.path.join(FILE_PATH, 'sub.txt'), 'rb') as file:
            sub_content = file.read()
        logger.info(f"\n{sub_content.decode('utf-8')}")
    except FileNotFoundError:
        logger.error(f"sub.txt not found")
    
    logger.info(f'{FILE_PATH}/sub.txt saved successfully')
    time.sleep(20)

    # cleanup files
    files_to_delete = ['boot.log', 'list.txt', 'config.json', 'tunnel.yml', 'tunnel.json']
    for file_to_delete in files_to_delete:
        file_path_to_delete = os.path.join(FILE_PATH, file_to_delete)
        try:
            os.remove(file_path_to_delete)
            logger.info(f"{file_path_to_delete} has been deleted")
        except Exception as e:
            logger.error(f"Error deleting {file_path_to_delete}: {e}")

    logger.info('\033c')
    logger.info('App is running')
    logger.info('Thank you for using this script, enjoy!')
